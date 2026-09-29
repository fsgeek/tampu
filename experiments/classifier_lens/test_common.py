from experiments.classifier_lens.common import question, repeatability_sample, summarize


def test_question_substitutes_task_verbatim():
    q = question("Find X.")
    assert q == {"type": "noul", "instructions":
                 "A researcher is investigating this task: Find X.. Does this passage "
                 "contain information that would help complete the task?"}


def test_sample_is_seeded_and_adds_missing_probes():
    elements = [dict(ordinal=i, page=1, text=f"t{i}") for i in range(1000)]
    a, overlap_a = repeatability_sample(elements, [5, 999])
    b, overlap_b = repeatability_sample(elements, [5, 999])
    assert a == b and overlap_a == overlap_b
    ordinals = [e["ordinal"] for e in a]
    assert ordinals == sorted(ordinals)
    assert 5 in ordinals and 999 in ordinals
    assert len(a) == 200 + 2 - overlap_a


def test_summarize_counts_label_changes_and_spread():
    s = summarize({"a": [0.4, 0.6, 0.5], "b": [0.9, 0.9, 0.9], "c": [0.1, 0.2, 0.1]})
    assert s["label_changes_at_0_5"] == 1
    assert s["identical_all_repeats"] == 1
    assert abs(s["max_abs_diff"] - 0.2) < 1e-9
    assert abs(s["median_abs_diff"] - 0.1) < 1e-9
