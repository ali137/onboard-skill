import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import grade  # noqa: E402


def good():
    return {"questions": [{"id": i, "points": 1, "evidence": "x"} for i in range(1, 9)],
            "planted_claim_caught": True, "planted_claim_evidence": "y"}


def test_valid_accepts_good_reply():
    assert grade.valid(good()) == []


def test_valid_rejects_without_crashing():
    bad = []
    for mutate in [lambda r: r["questions"][0].update(points=True),
                   lambda r: r["questions"][0].update(points=1.0),
                   lambda r: r["questions"][0].update(id=None),
                   lambda r: r["questions"][0].update(id="1"),
                   lambda r: r["questions"][0].pop("evidence"),
                   lambda r: r["questions"].__setitem__(0, "not a dict"),
                   lambda r: r.pop("planted_claim_evidence"),
                   lambda r: r.update(extra=1),
                   lambda r: r.update(planted_claim_caught="yes"),
                   lambda r: r["questions"].pop()]:
        r = good()
        mutate(r)
        bad.append(grade.valid(r))
    assert all(bad), bad
    assert grade.valid(None) and grade.valid([]) and grade.valid("x")
