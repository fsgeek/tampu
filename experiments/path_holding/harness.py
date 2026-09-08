"""Bounded local research navigation. No setup or live-store fallback.

CLI: python harness.py RUN_DIR '{"op":"search","query":"..."}'
The trusted runner owns config.json; consumers use only this interface.
JSON byte counts exclude the CLI's final transport newline. Every invocation
is logged, including calls rejected after exhaustion or finalization.
navigation counts attempted navigation, including rejected/invalid calls;
valid finalize requests do not count as navigation. The runner bounds callers.
"""
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import time

ENDPOINT = 'http://127.0.0.1:18529'
FIELDS = {
    'search': {'op', 'query', 'scope', 'limit', 'since', 'until'},
    'recall': {'op', 'key'},
    'note': {'op', 'text', 'status'},
    'ledger': {'op', 'offset', 'limit'},
    'finalize': {'op', 'answer'},
}


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def _error(message, operation_id=None):
    return {'operation_id': operation_id, 'result': {'error': message}}


def _validate(request):
    if not isinstance(request, dict) or not isinstance(request.get('op'), str):
        raise ValueError('request must contain an op')
    op = request['op']
    if op not in FIELDS or set(request) - FIELDS[op]:
        raise ValueError('unknown operation or arguments')
    required = {'search': ('query',), 'recall': ('key',),
                'note': ('text', 'status'), 'ledger': (), 'finalize': ('answer',)}
    for name in required[op]:
        if name not in request:
            raise ValueError('missing ' + name)
    for name in ('query', 'scope', 'key', 'text', 'status', 'since', 'until'):
        if name in request and not (name in ('since', 'until') and request[name] is None):
            if not isinstance(request[name], str) or not request[name].strip():
                raise ValueError(name + ' must be a nonempty string')
    if 'limit' in request:
        if type(request['limit']) is not int or not 1 <= request['limit'] <= 10:
            raise ValueError('limit must be an integer from 1 to 10')
    if 'offset' in request:
        if type(request['offset']) is not int or request['offset'] < 0:
            raise ValueError('offset must be a nonnegative integer')
    return op


def _check_config(config):
    if config['endpoint'] != ENDPOINT:
        raise ValueError('endpoint must be ' + ENDPOINT)
    if config['arm'] not in ('control', 'record'):
        raise ValueError('invalid arm')
    if type(config['max_calls']) is not int or not 1 <= config['max_calls'] <= 20:
        raise ValueError('max_calls must be from 1 to 20')
    if not isinstance(config['max_seconds'], (int, float)) or not 0 < config['max_seconds'] <= 600:
        raise ValueError('max_seconds must be positive and at most 600')
    corpus = Path(config['corpus_path'])
    if not corpus.is_absolute():
        raise ValueError('corpus_path must be absolute')
    if hashlib.sha256(corpus.read_bytes()).hexdigest() != config['corpus_sha256']:
        raise ValueError('corpus hash mismatch')


def _retrieve(config, op, request):
    vendor = Path(config['vendor_path']).resolve()
    sys.path.insert(0, str(vendor))
    try:
        search_module = importlib.import_module('llm_memory.search')
        recall_module = importlib.import_module('llm_memory.recall')
    finally:
        sys.path.remove(str(vendor))
    for module in (search_module, recall_module):
        if not Path(module.__file__).resolve().is_relative_to(vendor):
            raise ValueError('loaded retrieval code differs from vendor_path')
    # In-memory only; preserve the copied source bytes for their frozen hashes.
    if 'SORT score DESC, doc._key ASC' not in search_module._AQL:
        search_module._AQL = search_module._AQL.replace('SORT score DESC', 'SORT score DESC, doc._key ASC')
    from arango import ArangoClient
    client = ArangoClient(hosts=ENDPOINT, request_timeout=30)
    try:
        db = client.db(config['database'], username='root', password='')
        if op == 'recall':
            return recall_module.recall(db, request['key'])
        return search_module.search(db, request['query'], scope=request.get('scope', 'all'),
                                    limit=request.get('limit', 2), since=request.get('since'),
                                    until=request.get('until'))
    finally:
        client.close()


def _compact(row):
    request, result = row['request'], row['output']['result']
    result = result if isinstance(result, dict) else {}
    op = request.get('op') if isinstance(request, dict) else None
    success = 'error' not in result
    return {
        'operation_id': row['operation_id'], 'request': request,
        'result_count': result.get('total') if op == 'search' and success else None,
        'returned_keys': [hit['key'] for hit in result.get('hits', [])] if op == 'search' else [],
        'inspected_key': request['key'] if op == 'recall' and success else None,
        'status': request['status'] if op == 'note' and success else ('ok' if success else 'error'),
    }


def invoke(run: Path, request: dict) -> dict:
    """Return a wrapped result and append every attempt under an exclusive lock."""
    request_json = _json(request)
    request_json.encode('utf-8')  # Reject non-JSON caller values before any side effects.
    return _invoke(Path(run), request, request_json)


def _invoke(run, request, request_json):
    with (run / '.lock').open('a', encoding='utf-8') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        started = time.time()
        clock_start = time.monotonic()
        config = json.loads((run / 'config.json').read_text(encoding='utf-8'))
        log_path = run / 'operations.jsonl'
        rows = [json.loads(line) for line in log_path.read_text(encoding='utf-8').splitlines()] if log_path.exists() else []
        validation_error = None
        try:
            op = _validate(request)
        except ValueError as exc:
            op, validation_error = None, str(exc)
        navigation = op != 'finalize'
        # Counter is derived only from the append-only operation record.
        count = sum(row['navigation'] for row in rows)
        anchor = config.get('started_at', rows[0]['started_at'] if rows else started)
        operation_id = len(rows) + 1
        try:
            if (run / 'answer.json').exists():
                raise ValueError('run already finalized')
            if navigation and count >= min(config['max_calls'], 20):
                raise ValueError('navigation budget exhausted')
            if navigation and started - anchor >= min(config['max_seconds'], 600):
                raise ValueError('navigation time exhausted')
            _check_config(config)
            if validation_error:
                raise ValueError(validation_error)
            if op == 'ledger':
                if config['arm'] != 'record':
                    raise ValueError('ledger is unavailable in control arm')
                offset, limit = request.get('offset', 0), request.get('limit', 10)
                result = {'total': len(rows), 'entries': [_compact(row) for row in rows[offset:offset + limit]]}
            elif op == 'note':
                result = {'text': request['text'], 'status': request['status']}
            elif op == 'finalize':
                # Finalization closes access before another ledger can expose the answer.
                (run / 'answer.json').write_text(_json(request['answer']) + '\n', encoding='utf-8')
                result = {'finalized': True}
            else:
                if op == 'recall':
                    seen = {key for row in rows for key in _compact(row)['returned_keys']}
                    if request['key'] not in seen:
                        raise ValueError('recall requires a key returned by this run search')
                result = _retrieve(config, op, request)
            output = {'operation_id': operation_id, 'result': result}
        except ValueError as exc:
            output = _error(str(exc), operation_id)
        except Exception as exc:
            # No connection strings, filesystem paths, or hidden data in errors.
            output = _error('infrastructure error: ' + type(exc).__name__, operation_id)
        response_json = _json(output)
        row = dict(operation_id=operation_id, navigation=navigation, request=request,
                   output=output, request_json=request_json, response_json=response_json,
                   request_bytes=len(request_json.encode('utf-8')),
                   response_bytes=len(response_json.encode('utf-8')),
                   started_at=started, ended_at=time.time(),
                   duration_seconds=time.monotonic() - clock_start)
        with log_path.open('a', encoding='utf-8') as log:
            log.write(_json(row) + '\n')
            log.flush()
            os.fsync(log.fileno())
        return output


def main():
    if len(sys.argv) != 3:
        raise SystemExit('usage: harness.py RUN_DIR JSON_REQUEST')
    raw = sys.argv[2]
    try:
        request = json.loads(raw)
        # json.loads accepts nonfinite numbers and escaped lone surrogates;
        # neither can enter our strict UTF-8 JSON audit record.
        _json(request).encode('utf-8')
    except ValueError:
        request = None  # malformed attempts still consume a navigation call
    print(_json(_invoke(Path(sys.argv[1]), request, raw)))


if __name__ == '__main__':
    main()
