"""Behavioral integration tests; touches only a unique disposable database."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from arango import ArangoClient

SOURCE = Path('/home/tony/projects/llm-memory')
sys.path.insert(0, str(SOURCE))
from llm_memory.index import ensure_index

HARNESS = Path(__file__).with_name('harness.py')


@pytest.fixture
def invoke():
    def call(run, payload):
        assert HARNESS.exists(), 'the navigation harness has not been implemented'
        spec = importlib.util.spec_from_file_location('pilot_harness', HARNESS)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.invoke(run, payload)
    return call


@pytest.fixture
def runs(tmp_path):
    client = ArangoClient(hosts='http://127.0.0.1:18529')
    system = client.db('_system', username='root', password='')
    name = 'path_pilot_test_' + uuid.uuid4().hex
    system.create_database(name)
    db = client.db(name, username='root', password='')
    ensure_index(db)
    docs = [dict(_key=key, cycle=i, ts=date, experiment_label=scope,
                 source_file='fixture.jsonl', user_message='amber question',
                 response='amber SECRET_EPISODE_BODY', state_text='')
            for i, (key, date, scope) in enumerate([
                ('a', '2026-01-01', 'alpha'), ('b', '2026-02-01', 'alpha'),
                ('c', '2026-03-01', 'beta')])]
    db.collection('episodes').insert_many(docs)
    corpus = tmp_path / 'corpus.json'
    corpus.write_text(json.dumps(docs))
    paths = {}
    for arm in ('control', 'record'):
        run = tmp_path / arm
        run.mkdir()
        (run / 'config.json').write_text(json.dumps(dict(
            arm=arm, endpoint='http://127.0.0.1:18529', database=name,
            vendor_path=str(SOURCE), corpus_path=str(corpus),
            corpus_sha256=hashlib.sha256(corpus.read_bytes()).hexdigest(),
            max_calls=20, max_seconds=600)))
        paths[arm] = run
    try:
        yield paths
    finally:
        system.delete_database(name)
        client.close()


def configure(run, **changes):
    path = run / 'config.json'
    config = json.loads(path.read_text())
    config.update(changes)
    path.write_text(json.dumps(config))


def logs(run):
    path = run / 'operations.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def test_search_full_count_stable_ties_and_arm_parity(invoke, runs):
    request = dict(op='search', query='amber', limit=2)
    control = invoke(runs['control'], request)
    record = invoke(runs['record'], request)
    assert control == record
    assert control['result']['total'] == 3
    assert [h['key'] for h in control['result']['hits']] == ['a', 'b']
    assert invoke(runs['record'], request)['result'] == record['result']


def test_search_scope_dates_and_full_recall(invoke, runs):
    run = runs['record']
    result = invoke(run, dict(op='search', query='amber', scope='alpha',
                              since='2026-02-01', until='2026-03-01'))['result']
    assert result['total'] == 1
    assert result['hits'][0]['key'] == 'b'
    recalled = invoke(run, dict(op='recall', key='b'))['result']
    assert recalled['response'] == 'amber SECRET_EPISODE_BODY'
    assert recalled['ts'] == '2026-02-01'
    assert 'error' in invoke(run, dict(op='recall', key='c'))['result']


def test_ledger_only_prior_local_operations_no_episode_text(invoke, runs):
    run = runs['record']
    invoke(run, dict(op='search', query='amber', limit=1))
    invoke(run, dict(op='recall', key='a'))
    invoke(run, dict(op='note', text='Consumer branch declaration', status='open'))
    invoke(runs['control'], dict(op='note', text='OTHER_RUN_SECRET', status='closed'))
    ledger = invoke(run, dict(op='ledger'))['result']
    assert ledger['total'] == 3
    assert [entry['operation_id'] for entry in ledger['entries']] == [1, 2, 3]
    assert ledger['entries'][0]['returned_keys'] == ['a']
    assert ledger['entries'][0]['result_count'] == 3
    assert ledger['entries'][1]['inspected_key'] == 'a'
    assert ledger['entries'][2]['status'] == 'open'
    assert ledger['entries'][2]['request']['text'] == 'Consumer branch declaration'
    serialized = json.dumps(ledger)
    assert 'SECRET_EPISODE_BODY' not in serialized
    assert 'OTHER_RUN_SECRET' not in serialized
    assert '"b"' not in serialized and '"c"' not in serialized
    page = invoke(run, dict(op='ledger', offset=1, limit=1))['result']
    assert len(page['entries']) == 1 and page['entries'][0]['operation_id'] == 2


def test_denied_and_invalid_calls_consume_budget_finalize_survives(invoke, runs):
    run = runs['control']
    configure(run, max_calls=2)
    assert 'error' in invoke(run, dict(op='ledger'))['result']
    assert 'error' in invoke(run, dict(op='search', query='amber', limit=0))['result']
    assert len(logs(run)) == 2
    rejected = invoke(run, dict(op='note', text='too late', status='open'))
    assert rejected['result']['error'] == 'navigation budget exhausted'
    assert len(logs(run)) == 3
    assert logs(run)[-1]['output'] == rejected
    assert logs(run)[-1]['navigation'] is True
    answer = {'claims': ['an answer'], 'citations': []}
    assert invoke(run, dict(op='finalize', answer=answer))['result']['finalized']
    assert json.loads((run / 'answer.json').read_text()) == answer
    assert len(logs(run)) == 4
    assert 'error' in invoke(run, dict(op='search', query='amber'))['result']
    terminal_rejection = invoke(run, dict(op='finalize', answer='overwrite'))
    assert 'error' in terminal_rejection['result']
    rows = logs(run)
    assert [row['operation_id'] for row in rows] == [1, 2, 3, 4, 5, 6]
    assert rows[-1]['output'] == terminal_rejection
    assert rows[-1]['navigation'] is False
    assert rows[-1]['response_bytes'] == len(rows[-1]['response_json'].encode('utf-8'))
    assert json.loads((run / 'answer.json').read_text()) == answer


def test_time_limit_uses_config_anchor_and_still_allows_finalize(invoke, runs):
    run = runs['record']
    configure(run, started_at=time.time() - 601)
    rejected = invoke(run, dict(op='search', query='amber'))
    assert rejected['result']['error'] == 'navigation time exhausted'
    assert logs(run)[-1]['output'] == rejected
    assert logs(run)[-1]['navigation'] is True
    assert invoke(run, dict(op='finalize', answer='abstain'))['result']['finalized']


def test_hash_and_endpoint_tamper_fail_before_retrieval(invoke, runs):
    run = runs['record']
    config = json.loads((run / 'config.json').read_text())
    Path(config['corpus_path']).write_text('tampered')
    assert invoke(run, dict(op='search', query='amber'))['result']['error'] == 'corpus hash mismatch'
    assert invoke(run, dict(op='finalize', answer='answer'))['result']['error'] == 'corpus hash mismatch'
    assert not (run / 'answer.json').exists()
    configure(run, endpoint='http://127.0.0.1:8529')
    assert invoke(run, dict(op='search', query='amber'))['result']['error'] == 'endpoint must be http://127.0.0.1:18529'


@pytest.mark.parametrize('payload', [
    {'op': 'search', 'query': 'amber', 'limit': 11},
    {'op': 'search', 'query': 'amber', 'limit': True},
    {'op': 'search', 'query': 'amber', 'run': '../control'},
    {'op': 'ledger', 'offset': -1}, {'op': 'ledger', 'limit': 11},
    {'op': 'recall', 'key': '../secret'}, {'op': 'note', 'text': 'missing status'},
    {'op': 'unknown'},
])
def test_invalid_calls_are_logged_and_counted(invoke, runs, payload):
    result = invoke(runs['record'], payload)
    assert result['operation_id'] == 1 and 'error' in result['result']
    assert len(logs(runs['record'])) == 1


def test_cli_preserves_request_and_response_bytes(invoke, runs):
    raw = '{ "op" : "note", "text" : "café", "status" : "open" }'
    process = subprocess.run([sys.executable, str(HARNESS), str(runs['control']), raw],
                             capture_output=True, check=True)
    output = json.loads(process.stdout)
    row = logs(runs['control'])[0]
    assert row['request_json'] == raw
    assert row['request_bytes'] == len(raw.encode())
    assert row['response_json'].encode() + b'\n' == process.stdout
    assert row['response_bytes'] == len(process.stdout) - 1
    assert row['output'] == output
    assert row['ended_at'] >= row['started_at']
    assert row['duration_seconds'] >= 0


def test_concurrent_calls_do_not_lose_budget_or_ids(invoke, runs):
    run = runs['record']
    configure(run, max_calls=4)
    with ThreadPoolExecutor(max_workers=8) as pool:
        outputs = list(pool.map(lambda _: invoke(run, dict(op='note', text='x', status='open')), range(8)))
    rows = logs(run)
    assert [r['operation_id'] for r in rows] == list(range(1, 9))
    assert sum('error' not in output['result'] for output in outputs) == 4


def test_cli_exhaustion_is_logged_with_exact_response_bytes(invoke, runs):
    run = runs['control']
    configure(run, max_calls=1)
    invoke(run, dict(op='note', text='first', status='open'))
    raw = '{ "op": "search", "query": "amber" }'
    process = subprocess.run([sys.executable, str(HARNESS), str(run), raw],
                             capture_output=True, check=True)
    output = json.loads(process.stdout)
    assert output['result']['error'] == 'navigation budget exhausted'
    row = logs(run)[-1]
    assert row['operation_id'] == 2
    assert row['output'] == output
    assert row['request_json'] == raw
    assert row['request_bytes'] == len(raw.encode('utf-8'))
    assert row['response_json'].encode('utf-8') + b'\n' == process.stdout
    assert row['response_bytes'] == len(process.stdout) - 1


@pytest.mark.parametrize('raw', [
    '{"op":"finalize","answer":NaN}',
    '{"op":"note","text":"\\ud800","status":"open"}',
])
def test_cli_nonfinite_and_lone_surrogate_are_logged_malformed_attempts(invoke, runs, raw):
    run = runs['record']
    configure(run, max_calls=1)
    process = subprocess.run([sys.executable, str(HARNESS), str(run), raw],
                             capture_output=True)
    assert process.returncode == 0, process.stderr.decode('utf-8')
    output = json.loads(process.stdout)
    assert 'error' in output['result']
    row = logs(run)[-1]
    assert row['operation_id'] == 1
    assert row['navigation'] is True
    assert row['request_json'] == raw
    assert row['request_bytes'] == len(raw.encode('utf-8'))
    assert row['output'] == output
    assert row['response_json'].encode('utf-8') + b'\n' == process.stdout
    assert row['response_bytes'] == len(process.stdout) - 1
    assert not (run / 'answer.json').exists()
    rejected = invoke(run, dict(op='search', query='amber'))
    assert rejected['result']['error'] == 'navigation budget exhausted'


@pytest.mark.parametrize('value', [float('nan'), '\ud800'])
def test_programmatic_non_json_value_is_rejected_before_side_effects(invoke, runs, value):
    run = runs['record']
    with pytest.raises(ValueError):
        invoke(run, dict(op='finalize', answer=value))
    assert not logs(run)
    assert not (run / 'answer.json').exists()
