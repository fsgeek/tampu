"""Export CLM inputs owner-locally: element texts per artifact and the
repeatability sample, identical to the one Jev used."""
import argparse
import json
from pathlib import Path

from experiments.classifier_lens.common import load_cases, nonempty_elements, question, repeatability_sample, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    from tampu.config import load_config
    from tampu.repository import Repository
    repo = Repository(load_config(), initialize=False)
    data = {}
    for case in load_cases()["cases"]:
        probes = case["assessment_probes"]
        elements = nonempty_elements(repo, probes[0]["projection_id"])
        sample, _ = repeatability_sample(elements, [p["ordinal"] for p in probes])
        data[case["id"]] = dict(question=question(case["task"]),
                                elements=[dict(ordinal=e["ordinal"], text=e["text"]) for e in elements],
                                repeat_sample=[e["ordinal"] for e in sample])
    text = json.dumps(data)
    args.out.write_text(text)
    print("wrote", args.out, "sha256", sha(text), {k: len(v["elements"]) for k, v in data.items()})


if __name__ == "__main__":
    main()
