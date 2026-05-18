"""Deterministic synthesis validator + centroid fallback for SPORK Pro mode.

Invoked by SKILL.md after every synthesis step in Fire God / Token Gobbler / Full
Stack tiers. Three jobs:

  1. verify_synthesis(synthesis, inputs)  -> (ok, errors)
     Three checks per the Shield (b) policy in references/pro-mode-recovery.md:
       a. citation existence  - every cited ID in [1, N]
       b. citation grounding  - Jaccard >= 0.3 on cited (field, ID) pairs
       c. dedup integrity     - every input option appears in exactly one cluster
                                 (pass-2 only)

  2. centroid_pass1(digests)  -> digest
     Jaccard-centroid pick over the 10 digests.

  3. centroid_pass2(options)  -> 5 cluster centroids
     Greedy title-overlap clustering until 5 clusters emerge.

No LLM calls. No network. Standard library only (PyYAML or json input).

Usage from SKILL.md (Bash tool):

    python skills/spork/lib/verify_synthesis.py verify <synthesis.yaml> <inputs.yaml>
    python skills/spork/lib/verify_synthesis.py centroid-pass1 <inputs.yaml>
    python skills/spork/lib/verify_synthesis.py centroid-pass2 <inputs.yaml>

Inputs.yaml: a YAML list of input agent outputs (each item is one agent's payload).
Synthesis.yaml: the synthesised output to validate (must include citation_map).

Exit codes:
  0 - ok / centroid produced
  1 - validation failed (errors printed to stdout as JSON)
  2 - tooling / parse error
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # PyYAML
except ImportError:
    yaml = None


# --------------------------------------------------------------------------
# Tokenisation
# --------------------------------------------------------------------------

STOP_WORDS = frozenset(
    "a an the and or but if of for to in on at by with from into onto "
    "is are was were be been being do does did have has had this that "
    "these those it its as not no so than then there here we you they "
    "i he she him her them our your their which what who whom whose "
    "while when where why how all any some each every both either "
    "neither very much more most less least just only also even still "
    "can could may might must shall should will would".split()
)

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")


def tokens(text: str) -> set[str]:
    """Lowercase content-word tokens, stop-words removed, length >= 3."""
    if not text:
        return set()
    return {
        w.lower()
        for w in _WORD_RE.findall(text)
        if len(w) >= 3 and w.lower() not in STOP_WORDS
    }


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------


def load_yaml(path: str | Path) -> Any:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text)
    # Fallback: try JSON. SKILL.md may dump synthesis as JSON if PyYAML unavailable.
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"PyYAML not installed and {path} is not valid JSON: {e}"
        ) from e


# --------------------------------------------------------------------------
# verify_synthesis
# --------------------------------------------------------------------------


def verify_synthesis(synthesis: dict, inputs: list[dict]) -> tuple[bool, list[str]]:
    """Validate that synthesis is grounded in inputs.

    Returns (ok, errors). Errors is empty when ok=True.
    """
    errors: list[str] = []
    n = len(inputs)

    if not isinstance(synthesis, dict):
        return False, [f"synthesis is not a mapping (got {type(synthesis).__name__})"]
    if not isinstance(inputs, list) or n == 0:
        return False, ["inputs must be a non-empty list"]

    citation_map = synthesis.get("citation_map")
    if not isinstance(citation_map, dict) or not citation_map:
        return False, ["synthesis.citation_map missing or empty"]

    # Check 1: citation existence
    for field, cited in citation_map.items():
        if not isinstance(cited, list) or not cited:
            errors.append(f"citation_map[{field!r}] is not a non-empty list")
            continue
        for cid in cited:
            if not isinstance(cid, int):
                errors.append(
                    f"citation_map[{field!r}] contains non-integer ID {cid!r}"
                )
                continue
            if cid < 1 or cid > n:
                errors.append(
                    f"citation_map[{field!r}] cites ID {cid} out of range [1, {n}]"
                )

    if errors:
        # Bail before grounding check if existence is broken
        return False, errors

    # Check 2: citation grounding (Jaccard >= 0.3)
    # citation_map keys are dotted paths relative to the INPUT shape (since
    # synthesis re-emits the same schema as inputs). The synthesised field is
    # found at synthesized_digest.<path> if that wrapper exists, else at <path>.
    #
    # Grounding is only checked when the field has a direct correspondent in
    # the input shape (e.g. digest.situation). Synthesis-only fields like
    # `disagreements` (meta-observations about cluster diversity) and
    # `cluster_assignments` (structural maps) are exempted — their content has
    # no direct token correspondent in the inputs. Existence of valid citations
    # still validates them; the deeper grounding for synthesis-only fields is
    # delegated to (a) the dedup integrity check (for cluster_assignments) and
    # (b) human review at the picker (for disagreements, critic_notes, etc.).
    NO_GROUNDING_CHECK = {
        "cluster_assignments",
        "disagreements",
        "critic_notes",
        "objections",
        "arguments",
        "bottom_clusters_argued_for",
        "recommended_cluster_id",
    }
    syn_wrapper = (
        synthesis.get("synthesized_digest")
        if isinstance(synthesis.get("synthesized_digest"), dict)
        else synthesis
    )
    for field, cited in citation_map.items():
        if field in NO_GROUNDING_CHECK:
            continue
        syn_value = _walk(syn_wrapper, field)
        if syn_value is None:
            syn_value = _walk(synthesis, field)
        syn_tokens = tokens(_stringify(syn_value))
        if not syn_tokens:
            continue
        best_score = 0.0
        for cid in cited:
            input_value = _walk(inputs[cid - 1], field)
            input_tokens = tokens(_stringify(input_value))
            score = jaccard(syn_tokens, input_tokens)
            if score > best_score:
                best_score = score
        if best_score < 0.3:
            errors.append(
                f"citation_map[{field!r}]: best Jaccard {best_score:.2f} < 0.3 "
                f"across cited IDs {cited} - synthesised content not grounded"
            )

    # Check 3: dedup integrity (pass-2 only)
    cluster_assignments = synthesis.get("cluster_assignments")
    if cluster_assignments is not None:
        # Expect: {input_id: cluster_id} mapping every input option to one cluster
        # Inputs in pass-2 are leverage agent outputs; each has a leverage_options
        # list. Total options = sum of len(leverage_options) across inputs.
        all_option_ids: set[str] = set()
        for i, inp in enumerate(inputs, start=1):
            opts = (inp or {}).get("leverage_options") or []
            for j, _opt in enumerate(opts):
                all_option_ids.add(f"{i}.{j}")

        if not isinstance(cluster_assignments, dict):
            errors.append("cluster_assignments must be a mapping")
        else:
            assigned_ids = set(cluster_assignments.keys())
            missing = all_option_ids - assigned_ids
            extra = assigned_ids - all_option_ids
            if missing:
                errors.append(
                    f"dedup integrity: {len(missing)} input options not assigned "
                    f"to any cluster (e.g. {sorted(missing)[:5]})"
                )
            if extra:
                errors.append(
                    f"dedup integrity: {len(extra)} cluster assignments reference "
                    f"options no input agent produced (e.g. {sorted(extra)[:5]})"
                )
            # Each option must appear in exactly one cluster
            for opt_id, cluster in cluster_assignments.items():
                if isinstance(cluster, list) and len(cluster) > 1:
                    errors.append(
                        f"dedup integrity: option {opt_id} assigned to multiple "
                        f"clusters {cluster}"
                    )

    return (not errors), errors


def _walk(obj: Any, dotted: str) -> Any:
    """Walk obj['a']['b']['c'] given dotted='a.b.c'. Returns None on miss."""
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return " ".join(_stringify(v) for v in value)
    if isinstance(value, dict):
        return " ".join(f"{k} {_stringify(v)}" for k, v in value.items())
    return str(value)


# --------------------------------------------------------------------------
# centroid_pass1
# --------------------------------------------------------------------------


def centroid_pass1(digests: list[dict]) -> dict:
    """Pick the digest with highest mean Jaccard to the other nine.

    Each digest is expected to be a dict with a top-level 'digest' key holding
    {situation, goal, key_constraints, success_looks_like}.
    """
    if not digests:
        raise ValueError("digests must be non-empty")
    if len(digests) == 1:
        return digests[0]

    bags = [_digest_bag(d) for d in digests]
    best_i = 0
    best_mean = -1.0
    for i, bi in enumerate(bags):
        others = [jaccard(bi, bj) for j, bj in enumerate(bags) if j != i]
        mean = sum(others) / len(others)
        if mean > best_mean:
            best_mean = mean
            best_i = i
    return digests[best_i]


def _digest_bag(d: dict) -> set[str]:
    body = d.get("digest", d) if isinstance(d, dict) else {}
    return tokens(_stringify(body))


# --------------------------------------------------------------------------
# centroid_pass2
# --------------------------------------------------------------------------


def centroid_pass2(options: list[dict]) -> list[dict]:
    """Greedy title-overlap clustering. Returns 5 cluster centroids.

    `options` is the flat list of all leverage options across the 10 pass-2
    inputs (each input contributes ~5 options; total ~50). Each option is a dict
    with at least a 'title' key.
    """
    if len(options) < 5:
        return options

    # Tokenise titles
    titled = [(opt, tokens(opt.get("title", ""))) for opt in options]

    # Greedy: pick the option whose title-tokens overlap most with un-clustered
    # peers; assign all peers with Jaccard > 0.3 to its cluster; repeat until
    # 5 clusters or no more options.
    clusters: list[list[tuple[dict, set[str]]]] = []
    remaining = list(titled)
    while remaining and len(clusters) < 5:
        # Best seed: option with highest mean Jaccard to remaining
        best_i = 0
        best_mean = -1.0
        for i, (_, bi) in enumerate(remaining):
            others = [
                jaccard(bi, bj)
                for j, (_, bj) in enumerate(remaining)
                if j != i
            ]
            mean = sum(others) / len(others) if others else 0.0
            if mean > best_mean:
                best_mean = mean
                best_i = i
        seed = remaining.pop(best_i)
        cluster = [seed]
        # Attach peers with Jaccard > 0.3 to the seed
        peers = []
        keep = []
        for rest in remaining:
            if jaccard(seed[1], rest[1]) > 0.3:
                peers.append(rest)
            else:
                keep.append(rest)
        cluster.extend(peers)
        remaining = keep
        clusters.append(cluster)

    # If remaining options exist and we hit 5 clusters, fold each into its
    # nearest existing cluster (so all 50 options end up assigned, satisfying
    # dedup integrity).
    for opt_bag in remaining:
        best_c = 0
        best_score = -1.0
        for c_idx, c in enumerate(clusters):
            seed_bag = c[0][1]
            score = jaccard(opt_bag[1], seed_bag)
            if score > best_score:
                best_score = score
                best_c = c_idx
        clusters[best_c].append(opt_bag)

    # Return one centroid option per cluster (the seed - highest mean Jaccard
    # within its cluster). Preserve the option dict.
    return [c[0][0] for c in clusters]


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]

    try:
        if cmd == "verify":
            if len(argv) != 4:
                print("usage: verify <synthesis.yaml> <inputs.yaml>", file=sys.stderr)
                return 2
            synthesis = load_yaml(argv[2])
            inputs = load_yaml(argv[3])
            if not isinstance(inputs, list):
                print("inputs must be a YAML list", file=sys.stderr)
                return 2
            ok, errors = verify_synthesis(synthesis, inputs)
            payload = {"ok": ok, "errors": errors}
            print(json.dumps(payload, indent=2))
            return 0 if ok else 1

        if cmd == "centroid-pass1":
            if len(argv) != 3:
                print("usage: centroid-pass1 <inputs.yaml>", file=sys.stderr)
                return 2
            digests = load_yaml(argv[2])
            if not isinstance(digests, list):
                print("inputs must be a YAML list of digests", file=sys.stderr)
                return 2
            chosen = centroid_pass1(digests)
            print(json.dumps(chosen, indent=2))
            return 0

        if cmd == "centroid-pass2":
            if len(argv) != 3:
                print("usage: centroid-pass2 <inputs.yaml>", file=sys.stderr)
                return 2
            inputs = load_yaml(argv[2])
            if not isinstance(inputs, list):
                print("inputs must be a YAML list of pass-2 agent outputs", file=sys.stderr)
                return 2
            # Flatten leverage_options across inputs
            flat: list[dict] = []
            for inp in inputs:
                opts = (inp or {}).get("leverage_options") or []
                flat.extend(opts)
            centroids = centroid_pass2(flat)
            print(json.dumps(centroids, indent=2))
            return 0

        print(f"unknown command: {cmd}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        return 2

    except RuntimeError as e:
        print(f"tooling error: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001 - CLI surface; map all to exit 2
        print(f"error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
