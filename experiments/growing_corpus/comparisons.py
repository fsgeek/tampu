"""Instantiate the fixed development masks from actual diagnostic Service responses."""

import argparse
import copy
import hashlib
import json
import random
from pathlib import Path

PROMPT = "You are reviewing one frozen lexical-search observation from a PDF collection. Answer the `question` in the payload using only the fields and evidence shown. The observation may omit information; do not infer omitted counts, coverage, aliases, processing status, or corpus completeness. A zero lexical match can support only a predicate-scoped statement when its searched representation and coverage warrant it; it does not prove that an idea is absent from source PDFs. A nonempty hit is evidence only for what its displayed passage supports. Return exactly one JSON object with these keys: `conclusion_class` (`present`, `bounded_negative`, or `unresolved`), `conclusion` (one sentence), `basis` (an array of zero to three shown field names or evidence labels), `next_step` (one sentence describing the single best feasible next action, or `stop`), and `confidence` (`low`, `medium`, or `high`). Do not mention this experiment, hidden conditions, or information not shown."


def canon(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(v):
    return hashlib.sha256(v).hexdigest()


def write(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + "\n")


def paths(v, p="$"):
    if isinstance(v, dict):
        return {q: w for k, x in v.items() for q, w in paths(x, p + "." + k).items()}
    if isinstance(v, list):
        return {
            q: w for k, x in enumerate(v) for q, w in paths(x, p + f"[{k}]").items()
        } or {p: []}
    return {p: v}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    obs = json.loads(args.observations.read_text())
    summary = json.loads((args.observations.parent / "summary.json").read_text())
    revision = next(
        r["revision"] for r in summary["records"] if r["collection"] == "comparison"
    )
    questions = {
        "present": "Does the displayed evidence support that Blind Oracle evicts the cached item predicted to be requested furthest in the future?",
        "absent": "Does the exact lexical phrase tampuabsentpredicateqxz have a match in the stated short-paper subset and searched representation?",
        "alias": "Does the collection support a prediction-guided Marker caching policy?",
        "processing_gap": "Does CORFU: A Distributed Shared Log support implementing a shared log across a cluster?",
    }
    public = dict(zip(questions, ["A", "B", "C", "D"], strict=True))
    payloads = {}
    sheet = []
    audit = []
    for case, question in questions.items():
        o = obs[case]
        r = o["response"]["result"]
        assert o["response"]["status"] == "ok" and r["count_kind"] == "exact"
        hits = [
            {
                k: h[k]
                for k in ["artifact_id", "source_aliases", "physical_page", "extract"]
            }
            for h in r["hits"]
        ]
        common = {
            "case": public[case],
            "question": question,
            "status": o["response"]["status"],
            "hits": hits,
            "observation": "One frozen lexical observation.",
        }
        identity = {
            "predicate": r["predicate"],
            "lens": r["lens"],
            "representation": r["lens_config"]["analyzer"],
            "revision_id": r["revision_id"],
            "projection_selection": r["projection_selection"],
            "selected_projections": [
                {"artifact_id": p["artifact_id"], "projection_id": p["projection_id"]}
                for p in o["projection_records"]
            ],
        }
        coverage = {
            "coverage": r["coverage"],
            "enumeration_complete": revision["enumeration_complete"],
            "projection_processing": [
                {
                    "artifact_id": p["artifact_id"],
                    "status": p["status"],
                    "coverage": p["coverage"],
                    "losses": p["losses"],
                }
                for p in o["projection_records"]
            ],
        }
        count = {"candidate_count": r["full_count"], "count_kind": r["count_kind"]}
        if case == "present":
            assert r["full_count"] > len(hits) > 0
            # The admitted displayed evidence includes the inspected original match text.
            common["inspected_evidence"] = {
                "label": "E1",
                **{
                    k: v
                    for k, v in o["inspection"]["result"]["evidence"].items()
                    if k
                    in [
                        "artifact_id",
                        "projection_id",
                        "ordinal",
                        "physical_page",
                        "start",
                        "end",
                        "text",
                    ]
                },
            }
        else:
            assert r["full_count"] == 0
        if case == "absent":
            assert r["coverage"]["pages_total"] == r["coverage"]["pages_with_text"] == 3
        if case == "processing_gap":
            assert (
                r["coverage"]["pages_with_text"] == 0
                and r["coverage"]["pages_total"] == 24
            )
        families = {"scope": ["scope_present", "scope_absent"]}
        if case in ["present", "processing_gap"]:
            families["count_coverage"] = [
                "neither",
                "count_only",
                "coverage_only",
                "combined",
            ]
        for family, arms in families.items():
            for arm in arms:
                payload = copy.deepcopy(common)
                if family == "scope":
                    payload.update(count)
                    if arm == "scope_present":
                        payload["scope"] = {**identity, **coverage}
                else:
                    payload["identity"] = copy.deepcopy(identity)
                    if arm in ["count_only", "combined"]:
                        payload.update(count)
                    if arm in ["coverage_only", "combined"]:
                        payload["coverage_scope"] = copy.deepcopy(coverage)
                label = f"{public[case]}-{family}-{arm}"
                payloads[label] = payload
                expected = (
                    "present"
                    if case == "present"
                    else (
                        "bounded_negative"
                        if case == "absent" and arm == "scope_present"
                        else "unresolved"
                    )
                )
                sheet.append(
                    {
                        "label": label,
                        "builder_case": case,
                        "family": family,
                        "arm": arm,
                        "question": question,
                        "expected_class": expected,
                        "class_points": 2,
                        "claim_boundary": {
                            "present": "Only the displayed Blind Oracle eviction rule.",
                            "absent": "Only the exact lexical predicate in the explicitly shown pinned representation and subset; masked scope warrants unresolved.",
                            "alias": "Concept unresolved; surface-form failure cannot establish absence. Do not invent the hidden alias hit.",
                            "processing_gap": "Source proposition unresolved; name zero text coverage only when shown. Do not invent an automatic fallback.",
                        }[case],
                        "feasible_next_steps": {
                            "present": [
                                "Inspect source context",
                                "Inspect known additional candidates when count is shown; requesting more evidence conditionally is also feasible without assuming hidden candidates",
                                "stop for the narrowly displayed rule",
                            ],
                            "absent": [
                                "stop only when complete predicate scope is shown",
                                "Request missing representation/scope evidence when hidden",
                            ],
                            "alias": [
                                "Try an independently proposed alias/paraphrase",
                                "Inspect potentially relevant source evidence",
                            ],
                            "processing_gap": [
                                "Request source review or explicit alternative extraction",
                                "Request missing coverage/scope when hidden",
                            ],
                        }[case],
                        "disallowed": [
                            "semantic absence",
                            "invented masked counts or coverage",
                            "automatic fallback",
                            "builder truth",
                        ],
                        "calibration_points": 1,
                        "next_step_points": 1,
                    }
                )
                body = canon(payload)
                (out / f"{label}.json").write_text(body + "\n")
                (out / f"{label}.txt").write_text(
                    PROMPT + "\n\n```json\n" + body + "\n```\n"
                )
                audit.append(
                    {
                        "label": label,
                        "payload_sha256": sha(body.encode()),
                        "file_sha256": sha((out / f"{label}.json").read_bytes()),
                        "prompt_sha256": sha((out / f"{label}.txt").read_bytes()),
                        "bytes": len(body.encode()),
                        "paths": paths(payload),
                        "top_level_schema": {
                            k: type(v).__name__ for k, v in payload.items()
                        },
                    }
                )
    # Exact allowed top-level intervention differences; all nested non-intervention
    # content must remain byte-identical. No opaque process-local handles are exposed.
    diffs = []
    for case in public.values():
        for family in ["scope", "count_coverage"]:
            group = [
                (k, v)
                for k, v in payloads.items()
                if k.startswith(case + "-" + family + "-")
            ]
            if not group:
                continue
            allowed = (
                {"scope"}
                if family == "scope"
                else {"candidate_count", "count_kind", "coverage_scope"}
            )
            stripped = [
                {k: v for k, v in payload.items() if k not in allowed}
                for _, payload in group
            ]
            assert all(canon(x) == canon(stripped[0]) for x in stripped)
            baseline = paths(group[0][1])
            for label, payload in group[1:]:
                pv = paths(payload)
                diff = {
                    key: {
                        "baseline": baseline.get(key, "<absent>"),
                        "arm": pv.get(key, "<absent>"),
                    }
                    for key in baseline.keys() | pv.keys()
                    if baseline.get(key, "<absent>") != pv.get(key, "<absent>")
                }
                diffs.append(
                    {"baseline": group[0][0], "arm": label, "path_value_diff": diff}
                )
    labels = list(payloads)
    random.Random(20260909).shuffle(labels)
    write(out / "case-sheet.json", sheet)
    write(
        out / "mask-audit.json",
        {
            "payloads": audit,
            "diffs": diffs,
            "direct_field_leakage_audit": "Allowlist drops opaque handles, all alternate counts/coverage, profile/recipe, omissions, summaries, scores, and cursors. Common evidence strips projection status; identity contains only stable hashes. Human string inspection required before execution.",
            "logical_overlap": "Visible hit length reveals returned hits; zero text coverage can imply zero lexical candidates. This is not information-theoretic concealment.",
        },
    )
    write(
        out / "freeze.json",
        {
            "seed": 20260909,
            "execution_order": labels,
            "provider_observations_sha256": sha(args.observations.read_bytes()),
            "provider_cases": {
                case: {
                    "request": obs[case]["request"],
                    "response_sha256": sha(canon(obs[case]["response"]).encode()),
                    "response_bytes": len(canon(obs[case]["response"]).encode()),
                    "timestamp": obs[case]["timestamp"],
                    "response_schema_version": "tampu-tools/v1 (Service constant, not an envelope field)",
                    "projection_recipes": [
                        {
                            "artifact_id": p["artifact_id"],
                            "projection_id": p["projection_id"],
                            "recipe": p["recipe"],
                        }
                        for p in obs[case]["projection_records"]
                    ],
                }
                for case in questions
            },
            "provider_observations_path": str(args.observations),
            "revision_id": revision["revision_id"],
            "model": "gpt-5.6-sol",
            "reasoning": "medium",
            "sampling": "CLI defaults",
            "numeric_output_cap": "Not exposed/configured by supported CLI route; identical default settings, retain truncation/termination",
            "case_sheet_sha256": sha((out / "case-sheet.json").read_bytes()),
            "mask_audit_sha256": sha((out / "mask-audit.json").read_bytes()),
            "common_prompt_sha256": sha(PROMPT.encode()),
            "payloads": [
                {k: v for k, v in a.items() if k not in ["paths", "top_level_schema"]}
                for a in audit
            ],
        },
    )
    print(json.dumps({"output": str(out), "payloads": len(payloads), "order": labels}))


if __name__ == "__main__":
    main()
