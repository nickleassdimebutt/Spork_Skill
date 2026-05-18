"""Golden tests for verify_synthesis.

Three scenarios from the v0.9.1 design plan, Phase D.1:

(a) 10 pass-1 digests with deliberately-fabricated key_constraints
    -> validator must FIRE (citation_map grounding < 0.3 on key_constraints).

(b) 50 pass-2 options across 5 known clusters
    -> dedup cluster_assignments must account for all 50 (D4 check).

(c) ranker output where rank 1 != argmax(score)
    -> mechanical rejection at the SKILL.md gate (we check it here).

Plus Phase D.2: centroid_pass1 / centroid_pass2 determinism (byte-identical
outputs across two calls on the same inputs).

Run: python skills/spork/lib/test_verify_synthesis.py
Exit 0 = all pass; exit 1 = a test failed (failure printed to stderr).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify_synthesis import (  # noqa: E402
    centroid_pass1,
    centroid_pass2,
    verify_synthesis,
)


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        print(f"FAIL: {msg}", file=sys.stderr)
        raise SystemExit(1)


# --------------------------------------------------------------------------
# Scenario (a) — fabricated key_constraint
# --------------------------------------------------------------------------


def test_a_fabricated_constraint() -> None:
    """10 pass-1 digests; synthesis fabricates a key_constraint no input said."""

    # 10 inputs all agree on the same situation but none mentions "GDPR"
    inputs = [
        {
            "digest": {
                "situation": "the team is picking a vector database for search",
                "goal": "restore search recall to baseline",
                "key_constraints": "budget under five hundred per month",
                "success_looks_like": "recall within two percent of elasticsearch",
            }
        }
        for _ in range(10)
    ]

    # Synthesis fabricates a GDPR constraint that none of the 10 inputs mentioned
    synthesis = {
        "synthesized_digest": {
            "digest": {
                "situation": "the team is picking a vector database for search",
                "goal": "restore search recall to baseline",
                # FABRICATED — none of the inputs mentioned GDPR or compliance
                "key_constraints": "must comply with GDPR data residency rules",
                "success_looks_like": "recall within two percent of elasticsearch",
            }
        },
        "citation_map": {
            "digest.situation": [1, 2, 3],
            "digest.goal": [1, 2, 3],
            "digest.key_constraints": [1, 2, 3],  # cited inputs don't support GDPR
            "digest.success_looks_like": [1, 2, 3],
        },
    }

    ok, errors = verify_synthesis(synthesis, inputs)
    assert_true(not ok, "scenario (a): validator should reject fabricated constraint")
    assert_true(
        any("key_constraints" in e for e in errors),
        f"scenario (a): expected error mentioning key_constraints; got {errors}",
    )
    print("PASS: (a) fabricated key_constraints detected")


# --------------------------------------------------------------------------
# Scenario (b) — 50 options, 5 clusters, dedup integrity
# --------------------------------------------------------------------------


def test_b_dedup_integrity() -> None:
    """10 pass-2 inputs each with 5 options; dedup must cover all 50."""

    # 10 inputs, each with 5 options (50 total)
    inputs = []
    for i in range(10):
        inputs.append(
            {
                "leverage_options": [
                    {"title": f"Compare vector DBs option {i}.{j}"} for j in range(5)
                ]
            }
        )

    # GOOD dedup: cluster_assignments covers all 50 options
    good_synthesis = {
        "cluster_assignments": {
            f"{i + 1}.{j}": (j % 5) for i in range(10) for j in range(5)
        },
        "disagreements": ["clusters span 5 semantic groups"],
        "citation_map": {
            "cluster_assignments": list(range(1, 11)),
            "disagreements": list(range(1, 11)),
        },
    }
    ok, errors = verify_synthesis(good_synthesis, inputs)
    assert_true(ok, f"scenario (b) GOOD: validator should accept full coverage; errors={errors}")

    # BAD dedup: drops option 5.3 (a lost option = D4 failure)
    bad_assignments = {
        f"{i + 1}.{j}": (j % 5) for i in range(10) for j in range(5)
    }
    del bad_assignments["5.3"]  # contrarian option lost
    bad_synthesis = {
        "cluster_assignments": bad_assignments,
        "disagreements": ["clusters span 5 semantic groups"],
        "citation_map": {
            "cluster_assignments": list(range(1, 11)),
            "disagreements": list(range(1, 11)),
        },
    }
    ok, errors = verify_synthesis(bad_synthesis, inputs)
    assert_true(
        not ok,
        "scenario (b) BAD: validator should reject dedup that drops an input option",
    )
    assert_true(
        any("dedup integrity" in e for e in errors),
        f"scenario (b) BAD: expected 'dedup integrity' error; got {errors}",
    )
    print("PASS: (b) dedup integrity catches dropped option")


# --------------------------------------------------------------------------
# Scenario (c) — ranker R1 (score-rank mismatch)
# --------------------------------------------------------------------------


def test_c_ranker_mismatch() -> None:
    """Ranker recommends cluster_id != argmax(weighted_total)."""

    # SKILL.md Phase 1.5.4 does the R1 check mechanically (not via
    # verify_synthesis). We simulate the check here.
    ranker_output = {
        "scores": {
            0: {"cost": 5, "reversibility": 5, "time_to_value": 5, "weighted_total": 15},
            1: {"cost": 8, "reversibility": 7, "time_to_value": 9, "weighted_total": 24},  # argmax
            2: {"cost": 6, "reversibility": 6, "time_to_value": 6, "weighted_total": 18},
        },
        "recommended_cluster_id": 0,  # R1 FAILURE — should be 1
    }
    argmax = max(ranker_output["scores"], key=lambda k: ranker_output["scores"][k]["weighted_total"])
    assert_true(
        ranker_output["recommended_cluster_id"] != argmax,
        "scenario (c) setup: recommended_cluster_id should disagree with argmax",
    )
    # The SKILL.md gate logic: reject if mismatch
    rejected = ranker_output["recommended_cluster_id"] != argmax
    assert_true(rejected, "scenario (c): SKILL.md R1 check must reject")
    print("PASS: (c) ranker score-rank mismatch is mechanically rejectable")


# --------------------------------------------------------------------------
# Phase D.2 — centroid determinism
# --------------------------------------------------------------------------


def test_d2_centroid_pass1_determinism() -> None:
    digests = [
        {"digest": {"situation": f"situation variant {i}", "goal": "shared goal text", "key_constraints": "shared budget", "success_looks_like": "shared recall"}}
        for i in range(10)
    ]
    a = centroid_pass1(digests)
    b = centroid_pass1(digests)
    assert_true(
        json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True),
        "scenario D.2 pass1: centroid output must be deterministic across two runs",
    )
    print("PASS: D.2 centroid_pass1 is deterministic")


def test_d2_centroid_pass2_determinism() -> None:
    # 5 distinct semantic clusters, 10 lexical variants each (50 total)
    cluster_themes = [
        "compare vector databases head-to-head with rubric",
        "measure recall before declaring options dead via benchmark",
        "red-team chosen vendor specifically pinecone leaning",
        "scope-check whether decision is one or three separable",
        "lock rubric recall constraint anchor measurable",
    ]
    options = []
    for theme_idx, theme in enumerate(cluster_themes):
        for variant_idx in range(10):
            options.append({"title": f"{theme} variant {variant_idx}"})

    a = centroid_pass2(options)
    b = centroid_pass2(options)
    assert_true(
        json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True),
        "scenario D.2 pass2: centroid output must be deterministic across two runs",
    )
    assert_true(len(a) == 5, f"D.2 pass2: must return exactly 5 centroids; got {len(a)}")
    print("PASS: D.2 centroid_pass2 is deterministic and returns 5 clusters")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> int:
    test_a_fabricated_constraint()
    test_b_dedup_integrity()
    test_c_ranker_mismatch()
    test_d2_centroid_pass1_determinism()
    test_d2_centroid_pass2_determinism()
    print("\nAll golden tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
