#!/usr/bin/env python
"""Diff two owner snapshots and rank what changed by cost of being wrong.

Sentence level, not line level, so reflowed paragraphs do not read as edits.
Every change is tagged MATERIAL or REWORDING by heuristic: a change is material
when it touches a number, a unit, a capability word, or a negation. The
heuristic ranks the work; it does not render the verdict. A human or an LLM
pass decides what a material change actually means.

    python tools/diff.py acme 2026-08-10 2026-08-21
    python tools/diff.py acme 2026-08-10 2026-08-21 --json out.json
"""
import argparse
import difflib
import json
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
    return Path(os.environ.get("CLAIM_CHECK_TARGETS", REPO / "targets"))

# A change is material when it moves a fact, not when it moves a word.
NUM = re.compile(r"\d")
UNIT = re.compile(r"\b(per|/)\s*(hour|day|week|month|year|user|seat|dev|developer|pr|review|repo)\b", re.I)
CAPABILITY = re.compile(
    r"\b(unlimited|included|supported|available|requires?|only|not|no|never|always|"
    r"cap(?:ped|s)?|limit(?:ed|s)?|free|beta|deprecated|soc\s?2|gdpr|hipaa|iso|"
    r"self-hosted|on-prem|air-?gapped|retention|stores?|encrypt)", re.I)

WS = re.compile(r"\s+")


def sentences(text):
    body = text.split("\n\n", 1)[-1]
    body = WS.sub(" ", body)
    parts = re.split(r"(?<=[.!?:])\s+(?=[A-Z0-9])|\s*\|\s*", body)
    return [p.strip() for p in parts if len(p.strip()) > 25]


def norm(s):
    return WS.sub(" ", s.lower().strip(" .,:;|"))


def material(s):
    return bool(NUM.search(s) or UNIT.search(s) or CAPABILITY.search(s))


def header(path):
    out = {}
    for line in path.read_text(encoding="utf-8").split("\n\n", 1)[0].splitlines():
        if ": " in line:
            k, v = line.split(": ", 1)
            out[k.strip().lower()] = v.strip()
    return out


def load(snapdir):
    pages = {}
    for f in sorted(snapdir.glob("*.txt")):
        h = header(f)
        url = h.get("source")
        if not url:
            continue
        pages[url.rstrip("/")] = {"file": f, "cls": h.get("class", "unknown"),
                                  "title": h.get("title", ""),
                                  "text": f.read_text(encoding="utf-8")}
    return pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--json")
    args = ap.parse_args()

    tdir = targets_root() / args.target
    cfg = yaml.safe_load((tdir / "owner.yaml").read_text(encoding="utf-8"))
    weight_of = {pc["id"]: pc.get("weight", "p2") for pc in cfg.get("page_classes", [])}

    a = load(tdir / "snapshots" / args.before)
    b = load(tdir / "snapshots" / args.after)

    added = sorted(set(b) - set(a))
    removed = sorted(set(a) - set(b))
    common = sorted(set(a) & set(b))

    findings = []
    for url in common:
        sa = [norm(s) for s in sentences(a[url]["text"])]
        sb_raw = sentences(b[url]["text"])
        sb = [norm(s) for s in sb_raw]
        if sa == sb:
            continue
        seta, setb = set(sa), set(sb)
        gone = [s for s in sa if s not in setb]
        new = [s for s in sb_raw if norm(s) not in seta]
        if not gone and not new:
            continue
        cls = b[url]["cls"]
        mat_new = [s for s in new if material(s)]
        mat_gone = [s for s in gone if material(s)]
        findings.append({
            "url": url, "cls": cls, "weight": weight_of.get(cls, "p2"),
            "added": new, "removed": gone,
            "material_added": mat_new, "material_removed": mat_gone,
            "kind": "MATERIAL" if (mat_new or mat_gone) else "REWORDING",
        })

    order = {"p0": 0, "p1": 1, "p2": 2}
    findings.sort(key=lambda f: (f["kind"] != "MATERIAL",
                                 order.get(f["weight"], 3),
                                 -(len(f["material_added"]) + len(f["material_removed"]))))

    mat = [f for f in findings if f["kind"] == "MATERIAL"]
    print(f"{args.before} -> {args.after}   {args.target}")
    print(f"pages: {len(a)} before, {len(b)} after "
          f"| added {len(added)} | removed {len(removed)} | changed {len(findings)}")
    print(f"changed pages carrying a material edit: {len(mat)}\n")

    if added:
        print("NEW PAGES")
        for u in added:
            print(f"  + [{b[u]['cls']}] {u}")
        print()
    if removed:
        print("PAGES GONE")
        for u in removed:
            print(f"  - [{a[u]['cls']}] {u}")
        print()

    for f in mat:
        print(f"[{f['weight'].upper()}] {f['cls']}  {f['url']}")
        for s in f["material_removed"][:6]:
            print(f"    was: {s[:150]}")
        for s in f["material_added"][:6]:
            print(f"    now: {s[:150]}")
        print()

    rew = [f for f in findings if f["kind"] == "REWORDING"]
    if rew:
        print(f"rewording only, no fact moved: {len(rew)} pages")
        for f in rew[:12]:
            print(f"    ~ [{f['cls']}] {f['url']}")

    if args.json:
        Path(args.json).write_text(json.dumps({
            "target": args.target, "before": args.before, "after": args.after,
            "added": added, "removed": removed, "findings": findings,
        }, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
