"""Shared inputs for the classifier lens diagnostic (frozen protocol, revision 2)."""
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE.parent / "artifact_local" / "cases.json"
SEED = 20260928
SAMPLE_SIZE = 200
JEV_MODEL = "jev-1.13.0"
TEMPLATE = ("A researcher is investigating this task: {task}. Does this passage "
            "contain information that would help complete the task?")


def load_cases():
    return json.loads(CASES.read_text())


def question(task):
    """The frozen Noul question payload. The task text is substituted verbatim."""
    return {"type": "noul", "instructions": TEMPLATE.format(task=task)}


def nonempty_elements(repo, projection_id):
    """Elements in ordinal order whose text is non-empty after stripping."""
    doc = repo.read_projection(projection_id, verify_bytes=True)
    raw = (repo.store / doc["elements_path"]).read_text()
    try:
        elements = json.loads(raw)
    except json.JSONDecodeError:
        elements = [json.loads(line) for line in raw.splitlines() if line.strip()]
    kept = [dict(ordinal=e["ordinal"], page=e["page"], text=e["text"].strip())
            for e in elements if e["text"].strip()]
    return sorted(kept, key=lambda e: e["ordinal"])


def repeatability_sample(elements, probe_ordinals):
    """200 seeded elements plus the artifact's probes, deduplicated, in ordinal order."""
    chosen = random.Random(SEED).sample(elements, SAMPLE_SIZE)
    ordinals = {e["ordinal"] for e in chosen}
    by_ordinal = {e["ordinal"]: e for e in elements}
    added = [by_ordinal[o] for o in probe_ordinals if o not in ordinals]
    return sorted(chosen + added, key=lambda e: e["ordinal"]), len(probe_ordinals) - len(added)


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def summarize(values_by_element):
    """values_by_element: {key: [p1, p2, p3]} -> label changes at 0.5 and |dp| stats."""
    diffs, changes = [], 0
    for values in values_by_element.values():
        diffs.append(max(values) - min(values))
        if len({v > 0.5 for v in values}) > 1:
            changes += 1
    diffs.sort()
    n = len(diffs)
    median = (diffs[(n - 1) // 2] + diffs[n // 2]) / 2 if n else None
    return dict(elements=n, label_changes_at_0_5=changes,
                identical_all_repeats=sum(d == 0 for d in diffs),
                median_abs_diff=median, max_abs_diff=diffs[-1] if n else None)
