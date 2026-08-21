#!/usr/bin/env python
"""Resolve whether each claim is still published on the owner's own site.

This closes the loop the claim registry leaves open. A claim has two independent
states, and conflating them produces the worst failure mode a weekly report has:
shouting about a problem somebody already fixed.

    status     is the claim TRUE?        (verified against the competitor)
    published  is the claim STILL SHOWN?  (verified against your own site)

OUT_OF_DATE + UNPUBLISHED is resolved, not urgent. OUT_OF_DATE + PUBLISHED is P0.

Claims are paraphrases of page copy, not quotes, so matching is by distinctive
token overlap plus a best-sentence similarity floor rather than exact string
search.

    python tools/published.py getoptimal 2026-08-21
    python tools/published.py getoptimal 2026-08-21 --write
"""
import argparse
import difflib
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent

def targets_root():
    """Targets may live outside the repo.

    The tool is public; a filled-in target is competitive research about a real
    company and usually is not. Set CLAIM_CHECK_TARGETS to keep findings in a
    private directory while the code stays shareable.
    """
    import os
    env = os.environ.get("CLAIM_CHECK_TARGETS")
    if env:
        return Path(env)
    # Single-target repo: config sits at the root next to the tools.
    if (REPO / "claims.yaml").exists():
        return REPO
    return REPO / "targets"

STOP = set("""a an and are as at be been but by can for from has have how in into is it its
me more most no not of on only or our out over per so than that the their them then there
these they this to up use used using was what when which who will with without you your
does do can't cannot only every each all""".split())

WS = re.compile(r"\s+")


def tokens(s):
    ws = re.findall(r"[a-z0-9][a-z0-9\-\./$%]*", s.lower())
    return [w for w in ws if w not in STOP and len(w) > 2]


def distinctive(claim):
    """Tokens that carry the claim: numbers, units, and uncommon words."""
    t = tokens(claim)
    return [w for w in t if any(c.isdigit() for c in w) or len(w) > 4]


def _one(snapdir, page_path):
    path = re.sub(r"^https?://[^/]+", "", page_path.strip()).split("(")[0].strip()
    slug = path.strip("/").replace("/", "__") or "index"
    f = snapdir / f"{slug}.txt"
    if not f.exists():
        return None
    return WS.sub(" ", f.read_text(encoding="utf-8").split("\n\n", 1)[-1]).lower()


def page_text(snapdir, page_field):
    """A claim may live on one page or many. Concatenate whatever resolves."""
    if isinstance(page_field, list):
        parts = page_field
    else:
        parts = [q for q in re.split(r",\s*", str(page_field)) if q.strip()]
    bodies = [b for b in (_one(snapdir, q) for q in parts) if b]
    return " ".join(bodies) if bodies else None


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\s\|\s", text) if len(s.strip()) > 20]


def resolve(claim_text, body):
    """Return (state, score, best_sentence)."""
    if body is None:
        return "PAGE_GONE", 0.0, ""
    dist = distinctive(claim_text)
    if not dist:
        return "UNKNOWN", 0.0, ""
    hits = [w for w in dist if w in body]
    cover = len(hits) / len(dist)
    best, ratio = "", 0.0
    ct = " ".join(tokens(claim_text))
    for s in sentences(body):
        r = difflib.SequenceMatcher(None, ct, " ".join(tokens(s))).ratio()
        if r > ratio:
            ratio, best = r, s
    score = max(cover, ratio)
    if cover >= 0.7 or ratio >= 0.55:
        return "PUBLISHED", score, best[:180]
    if cover <= 0.35 and ratio < 0.4:
        return "UNPUBLISHED", score, best[:180]
    return "AMBIGUOUS", score, best[:180]


# Severity is DERIVED. It is never a field in claims.yaml, because a hand-set severity
# drifts from the data the moment either input changes. Inputs: the verdict, whether the
# claim is still shown, and how expensive an error on that page class is.
SEV_RANK = {"p0": 0, "p1": 1, "p2": 2, "p3": 3}


def severity(claim, weight):
    st, pub = claim.get("status"), claim.get("published")
    if claim.get("source_type") == "internal":
        return "p3", "internal, never rechecked"
    if st in ("OUT_OF_DATE",) and pub == "PUBLISHED":
        return "p0", f"published and untrue on a {weight} page"
    if st == "internal_conflict":
        return "p0", "two of our own pages disagree"
    if st == "WEAKENED" and pub == "PUBLISHED":
        return "p1", "still true, argument blunted"
    if pub == "UNTRACKED":
        return "p1", "published with no claim behind it"
    if st in ("OUT_OF_DATE", "WEAKENED") and pub == "UNPUBLISHED":
        return "p3", "resolved, no longer published"
    if st == "UNVERIFIABLE":
        return "p3", "no source settles it"
    if pub == "AMBIGUOUS":
        return "p3", "needs a human read"
    return "p3", "current"


def page_weight(claim, cfg):
    pages = claim.get("page") if isinstance(claim.get("page"), list) else [claim.get("page")]
    best = "p2"
    for pc in cfg.get("page_classes", []):
        for m in pc.get("match", []):
            if any(m in str(q or "") for q in pages):
                w = pc.get("weight", "p2")
                if SEV_RANK.get(w, 3) < SEV_RANK.get(best, 3):
                    best = w
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("snapshot")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    root_dir = targets_root()
    tdir = root_dir if (root_dir / "claims.yaml").exists() or (root_dir / "owner.yaml").exists() else root_dir / args.target
    snap = tdir / "snapshots" / args.snapshot
    raw = (tdir / "claims.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(raw)

    counts, rows = {}, []
    for c in data["claims"]:
        if c.get("source_type") == "internal":
            state, score, best = "INTERNAL", 1.0, ""
        else:
            state, score, best = resolve(c["claim"], page_text(snap, c.get("page", "")))
        counts[state] = counts.get(state, 0) + 1
        rows.append((c, state, score, best))

    print(f"{args.target} claims vs snapshot {args.snapshot}")
    print("  " + " | ".join(f"{k} {v}" for k, v in sorted(counts.items())) + "\n")

    urgent = [(c, s, sc) for c, s, sc in ((r[0], r[1], r[2]) for r in rows)
              if s == "PUBLISHED" and c.get("status") in ("OUT_OF_DATE", "WEAKENED")]
    resolved = [(c, s) for c, s, _, _ in rows
                if s == "UNPUBLISHED" and c.get("status") in ("OUT_OF_DATE", "WEAKENED")]

    import yaml as _y
    ocfg = _y.safe_load((tdir / "owner.yaml").read_text(encoding="utf-8")) \
        if (tdir / "owner.yaml").exists() else {}
    sev_counts = {}
    for c, state, _, _ in rows:
        c2 = dict(c); c2["published"] = state
        sv, _why = severity(c2, page_weight(c2, ocfg))
        sev_counts[sv] = sev_counts.get(sv, 0) + 1
    print("derived severity: " + " | ".join(
        f"{k.upper()} {sev_counts[k]}" for k in sorted(sev_counts, key=lambda x: SEV_RANK[x])) + "\n")

    print(f"Published and no longer fully true: {len(urgent)} "
          f"(severity below; WEAKENED is P1, not P0)")
    for c, _, sc in sorted(urgent, key=lambda x: -x[2]):
        c2 = dict(c); c2["published"] = "PUBLISHED"
        sv, why = severity(c2, page_weight(c2, ocfg))
        print(f"  [{sv.upper()}] [{c['status']:12s}] {str(c['page'])[:26]:26s} {c['id']}  ({why})")
    print(f"\nResolved since authoring, no longer published: {len(resolved)}")
    for c, _ in resolved:
        print(f"  [{c['status']:12s}] {c['page']:28s} {c['id']}")

    amb = [(c, sc, b) for c, s, sc, b in rows if s == "AMBIGUOUS"]
    if amb:
        print(f"\nAmbiguous, needs a human read: {len(amb)}")
        for c, sc, b in amb:
            print(f"  {c['id']:26s} match {sc:.2f}  page says: {b[:90]}")

    if args.write:
        out = raw
        for c, state, score, _ in rows:
            if state in ("PAGE_GONE", "UNKNOWN"):
                continue
            pat = re.compile(rf"(^  - id: {re.escape(c['id'])}\n(?:.*\n)*?)(?=^  - id: |\Z)",
                             re.M)
            m = pat.search(out)
            if not m:
                continue
            blk = m.group(1)
            blk2 = re.sub(r"^    published: .*\n", "", blk, flags=re.M)
            blk2 = blk2.rstrip("\n") + f"\n    published: {state}\n"
            if not blk.rstrip().endswith("\n"):
                blk2 += ""
            out = out[:m.start(1)] + blk2 + out[m.end(1):]
        (tdir / "claims.yaml").write_text(out, encoding="utf-8")
        print(f"\nwrote published state into claims.yaml")


if __name__ == "__main__":
    main()
