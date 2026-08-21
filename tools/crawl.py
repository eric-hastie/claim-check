#!/usr/bin/env python
"""Crawl an owner site into a dated snapshot.

Config driven: reads targets/<slug>/owner.yaml. Writes
targets/<slug>/snapshots/<date>/ with one text file per page, an index, and a
meta.json recording what the run actually did.

Fails loudly. A run is a failure, not an all-clear, when a required anchor is
missing or the page count falls below the configured floor. A monitor that
quietly reports success while broken is worse than no monitor.

    python tools/crawl.py getoptimal
    python tools/crawl.py getoptimal --date 2026-08-21
"""
import argparse
import html as _html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from datetime import date as _date
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

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
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
SKIP_EXT = re.compile(
    r"\.(png|jpe?g|gif|svg|webp|ico|css|js|woff2?|ttf|mp4|pdf|zip|xml|json)$", re.I)


def fetch(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if "text/html" not in r.headers.get("Content-Type", ""):
                return None, r.status
            return r.read().decode("utf-8", "ignore"), r.status
    except urllib.error.HTTPError as e:
        return None, e.code
    except Exception:
        return None, None


def to_text(h):
    h = re.sub(r"(?is)<(script|style|svg|noscript)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?i)<(br|/p|/div|/h[1-6]|/li|/tr|/section)[^>]*>", "\n", h)
    h = re.sub(r"<[^>]+>", " ", h)
    h = _html.unescape(h)
    h = re.sub(r"[ \t]+", " ", h)
    return re.sub(r"\n\s*\n+", "\n\n", h).strip()


def strip_chrome(text, cfg):
    """Drop repeated nav and footer so a menu edit is not a content change."""
    for marker in cfg.get("strip_after") or []:
        i = text.find(marker)
        if 0 < i < len(text) * 0.4:
            j = text.rfind(marker, 0, int(len(text) * 0.45))
            text = text[j + len(marker):]
            break
    for foot in (cfg.get("strip_before_footer") or []) + ["© 20"]:
        k = text.rfind(foot)
        if k > len(text) * 0.5:
            text = text[:k]
            break
    return text.strip()


def slugify(url):
    p = unquote(urlparse(url).path).strip("/")
    return (p.replace("/", "__") or "index")[:110]


def classify(url, page_classes):
    path = urlparse(url).path or "/"
    for pc in page_classes:
        for m in pc.get("match", []):
            if m in path:
                return pc["id"], pc.get("mine", False), pc.get("weight", "p2")
    return "other", False, "p2"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--date", default=_date.today().isoformat())
    ap.add_argument("--max-pages", type=int)
    args = ap.parse_args()

    tdir = targets_root() / args.target
    cfg = yaml.safe_load((tdir / "owner.yaml").read_text(encoding="utf-8"))
    owner, ccfg = cfg["owner"], cfg.get("crawl", {})
    root = owner["root"].rstrip("/")
    classes = cfg.get("page_classes", [])
    max_pages = args.max_pages or ccfg.get("max_pages", 400)
    delay = ccfg.get("delay_seconds", 0.4)
    timeout = ccfg.get("timeout_seconds", 25)
    skips = ccfg.get("skip_paths", [])

    out = tdir / "snapshots" / args.date
    out.mkdir(parents=True, exist_ok=True)

    print(f"crawling {owner['name']} ({root}) -> {out}")
    seen, index, failures = set(), [], []
    q = deque([root + "/", root + "/llms.txt"])
    while q and len(index) < max_pages:
        url = q.popleft()
        norm = url.split("#")[0].rstrip("/") or root
        if norm in seen:
            continue
        seen.add(norm)
        h, status = fetch(url, timeout)
        time.sleep(delay)
        if not h:
            if status and status != 404:
                failures.append({"url": url, "status": status})
            continue
        text = strip_chrome(to_text(h), ccfg)
        title = (re.search(r"(?is)<title[^>]*>(.*?)</title>", h) or [None, ""])[1]
        title = _html.unescape(re.sub(r"\s+", " ", title)).strip()
        words = len(text.split())
        if words > 40:
            cls, mine, weight = classify(url, classes)
            (out / f"{slugify(url)}.txt").write_text(
                f"SOURCE: {url}\nTITLE: {title}\nCLASS: {cls}\n\n{text}\n",
                encoding="utf-8")
            index.append({"url": url, "title": title, "words": words,
                          "slug": slugify(url), "cls": cls, "mine": mine,
                          "weight": weight})
            print(f"  [{len(index):3d}] {words:5d}w  {cls:11s} {urlparse(url).path or '/'}")
        for m in re.finditer(r'href=["\']([^"\']+)', h):
            nxt = urljoin(url, m.group(1)).split("#")[0]
            if urlparse(nxt).netloc != urlparse(root).netloc:
                continue
            if SKIP_EXT.search(nxt) or any(s in nxt for s in skips):
                continue
            if nxt.split("#")[0].rstrip("/") not in seen:
                q.append(nxt)

    # ---- fail loudly -------------------------------------------------------
    problems = []
    floor = cfg.get("floor_pages", 0)
    if len(index) < floor:
        problems.append(f"page floor: saved {len(index)}, floor is {floor}")
    by_url = {r["url"].rstrip("/"): r for r in index}
    for req in cfg.get("required", []):
        rec = by_url.get(req["url"].rstrip("/"))
        if not rec:
            problems.append(f"required page never saved: {req['url']}")
            continue
        body = (out / f"{rec['slug']}.txt").read_text(encoding="utf-8")
        if req["anchor"] not in body:
            problems.append(
                f"anchor missing on {req['url']}: {req['anchor']!r} "
                f"(page returned {rec['words']} words)")

    meta = {"target": args.target, "date": args.date, "root": root,
            "urls_visited": len(seen), "pages_saved": len(index),
            "fetch_failures": failures, "problems": problems,
            "ok": not problems}
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    with (out / "index.tsv").open("w", encoding="utf-8") as f:
        f.write("url\tclass\tmine\tweight\twords\ttitle\n")
        for r in sorted(index, key=lambda x: x["url"]):
            f.write(f"{r['url']}\t{r['cls']}\t{r['mine']}\t{r['weight']}\t"
                    f"{r['words']}\t{r['title']}\n")

    print(f"\nvisited {len(seen)} urls, saved {len(index)} pages")
    if failures:
        print(f"fetch failures: {len(failures)}")
    if problems:
        print("\nRUN FAILED, this is not an all-clear:")
        for p in problems:
            print(f"  ! {p}")
        sys.exit(2)
    print("all required anchors present, page floor cleared")


if __name__ == "__main__":
    main()
