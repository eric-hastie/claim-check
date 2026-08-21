---
name: claim-check
description: Weekly verification that a comparison page's competitor claims are still true. Fetches the primary sources each claim depends on, renders a verdict per claim, updates claims.yaml, and writes a dated report of only what changed. Use when asked to run a claim check, verify competitor comparison pages, refresh a battlecard, or check whether a competitor shipped something that breaks a published claim.
---

# Claim check

A comparison page is a list of assertions about competitors. Each assertion has a
primary source that would settle it. This skill re-checks those sources on a schedule
and reports only the assertions whose status changed.

**It is not a page-change monitor.** Watching whole pages for diffs produces noise
(testimonial rotation, nav edits, A/B copy) and misses the changes that matter (a
competitor ships a feature and never edits the page you watch). Claims are the unit.

## Layout

This repository is one target: getoptimal.ai. Config and state sit at the root next to
the tools.

```
owner.yaml         the site being defended: page classes, anchors, page floor
competitors.yaml   who the digest watches
claims.yaml        input and state
snapshots/<date>/  one text file per page; git is the history
reports/<date>.md
tools/
```

To point the skill at a different company, set `CLAIM_CHECK_TARGETS` to a directory
holding the same four files. The tools read it if present and fall back to the repo root.

## Inputs

- `claims.yaml` is both the input and the state. Each claim carries `status`,
  `published`, `evidence` and `last_verified`. The job of a run is to update that file.
- `owner.yaml` defines your own site. Page classes decide two separate things: whether a
  page is **mined** for claims, and how expensive an error on it is (`weight`).
- `references/sources.md` says which URL is authoritative for which kind of claim, per
  competitor. Read it before fetching anything.

## Two states per claim, never one

This is the core of the design and the easiest thing to get wrong.

| | Question | Verified against |
|---|---|---|
| `status` | Is the claim TRUE? | the competitor's primary source |
| `published` | Is the claim STILL SHOWN? | your own site crawl |

`OUT_OF_DATE` + `PUBLISHED` is **P0**. `OUT_OF_DATE` + `UNPUBLISHED` is **resolved**,
and reporting it as urgent is the fastest way to make a weekly report unreadable. A
monitor that shouts about something already fixed gets ignored, and then it misses the
one that mattered.

`published` also carries `UNTRACKED`: an assertion found on a mined page with no claim
in the registry. An unverified published claim is a liability nobody has looked at, so
it is P1.

## Severity is derived, never hand-set

Severity falls out of the three fields already tracked. Do not add it as an independent
axis, because it will drift from the data.

| | What it is | Owner | Timebox |
|---|---|---|---|
| **P0** | Published and false. `OUT_OF_DATE` + `PUBLISHED`, or two of your own pages contradicting each other (`internal_conflict`). A prospect can disprove it in one click. | marketing, web | this week |
| **P1** | A competitor shipped something that changes how you sell. `WEAKENED` claims, digest items tagged `affects a claim`, and `UNTRACKED`. | sales | this cycle |
| **P2** | Competitive intel, no action. Becomes next quarter's claims. | everyone | none |
| **P3** | Housekeeping. Aging, failed fetches, ambiguous matches. Report as a **count**, not a list. | registry owner | monthly |

Within P0, order by the `weight` of the page class the claim sits on. A comparison or
pricing page outranks a docs page because the reader is further down the funnel.

## Procedure

### 1. Select

Build the run list. Include a claim if any of:
- it has never been verified,
- `last_verified` is more than 30 days ago,
- `status` is anything other than `CONFIRMED` (unresolved claims get rechecked every run),
- the operator named it explicitly.

Claims flagged `frozen: true` are skipped. Use that for strategic claims that only
change when a competitor reverses a public position.

**Claims with `source_type: internal` are never selected.** They come from customer
conversations, sales calls or proprietary data, and no public source will ever settle
them. Excluding them by construction is why this skill needs no escalation counter for
unverifiable claims: the only things left in the loop are claims a public source was
always expected to settle, so a persistent `UNVERIFIABLE` means a real problem with the
source rather than a claim that was never checkable. An internal claim published on a
public page still belongs in the file, marked, so nobody re-litigates its provenance
every quarter.

Print the run list with counts before fetching: total claims, selected, skipped, and why.

### 2. Fetch

Collect the deduplicated set of source URLs across selected claims, then fetch each one
once. Prefer changelogs and pricing pages over marketing pages: they are dated and
specific.

Record for every URL: fetched or failed, byte or word count, and the date on the newest
entry if it is a changelog.

**Fail loudly.** A fetch counts as failed if any of these is true:
- non-200, timeout, or redirect off-host,
- the extracted text is under 200 words for a page that previously exceeded it,
- an expected anchor string from `references/sources.md` is missing (this catches a
  JavaScript shell returning 200 with no content).

A failed fetch never becomes a verdict. Claims depending only on failed sources are set
to `UNVERIFIABLE` for this run with the reason recorded, and the report says so in the
coverage table. **Do not write a report that implies all-clear on a run where sources
failed.**

### 3. Verdict

For each selected claim, compare its text against the fetched sources and assign one of
four states. Never invent a fifth.

| Verdict | Means | Action for the owner |
|---|---|---|
| `CONFIRMED` | Sources still support the claim as written | None |
| `WEAKENED` | Still literally true, but a change materially blunts the argument built on it | Rewrite the framing, keep the row |
| `OUT_OF_DATE` | A source contradicts the claim | Fix or remove the row now |
| `UNVERIFIABLE` | Sources do not settle it, or a fetch failed | Do not publish the claim until settled |

`UNVERIFIABLE` is exempt from what follows, by definition: a claim no source settles has
no evidence date, no cause and no link to give. Record why the sources do not settle it
instead. Every **other** verdict must carry three things, or it is not finished:

1. **A date.** `evidence_date` is the date printed on the source: the changelog entry,
   the release post, the announcement. Never guess it and never substitute today's
   date. If the vendor published no date, write `undated` and let `observed` carry the
   report.
2. **A cause.** `competitor_shipped`, `source_check` or `internal_conflict`. These get
   fixed differently, and lumping them together hides the useful signal. A competitor
   shipping something is news; the other two are housekeeping.
3. **A link.** One URL the reader can open to see it themselves. Not a search, not a
   homepage, the page carrying the evidence.

Rules:
- Quote the evidence. A verdict without a quotable line and a URL is not a verdict.
- Prefer the competitor's own dated changelog entry over inference from a marketing page.
- Distinguish units. "5 reviews per developer" and "5 reviews per developer per hour"
  are different claims by three orders of magnitude. Read the unit, do not skim it.
- `WEAKENED` is the most common real outcome and the easiest to miss. A competitor
  adding a spend cap does not make "usage-based pricing" untrue, but it does kill a pitch
  built on unpredictable bills.
- Absence of evidence is not evidence. If a source is silent on a capability, that is
  `UNVERIFIABLE`, not `CONFIRMED`.

### 4. Update state

Rewrite `claims.yaml` in place: `status`, `cause`, `evidence` (one quotable line),
`source` (the URL a reader can open), `evidence_date`, `observed` (only on a status
change), and `last_verified` (today). Leave claims not selected this run untouched.

### 5. Report

Write `reports/YYYY-MM-DD.md` from `references/report_template.md`. The report contains
only deltas plus the coverage table.

**The first line is a verdict, not a greeting.** It is what someone reads in a Slack
notification without opening anything. Exactly one of:

```
NOTHING TO REPORT. 23 claims checked, all current. No competitor releases this week.
FYI ONLY. 2 competitor releases, no claim affected. Nothing to change.
ACTION NEEDED: 2 claims. Greptile shipped an analytics dashboard (2026-04-15).
```

Never open with "this week's report" or a restatement of the task. Never pad a quiet
week to look productive: a run that finds nothing is a good run and should read like
one, in a single line. Equally, never bury a real finding under a summary paragraph. If
a claim went out of date, the count and the competitor belong in the first sentence.

Render every finding with its date and its link, in this shape:

```
Out of date as of 2026-04-15 (Greptile changelog: "Analytics dashboard")
https://www.greptile.com/changelog
```

When `evidence_date` is `undated`, write "Out of date as of at least <observed>, no
dated announcement located." Never present an observation date as a release date.

Order findings by cost of being wrong: `OUT_OF_DATE` on a page with high inbound traffic
first, then `WEAKENED`, then `UNVERIFIABLE`, then aging.

### 6. Accounting

End every run with a reconciliation, in the report and in the reply:

```
claims total 21 | selected 18 | verdicts returned 18 | sources attempted 14 | fetched 13 | failed 1
```

If verdicts returned is less than selected, name the missing claims. Silent shrinkage
between these numbers is the failure mode this skill exists to prevent.

## Digest mode

Run with `--digest` to add a second section: **what competitors shipped in the window**,
whether or not it touches a claim. The changelogs are already being fetched, so this
costs one extra pass over material already in hand.

`competitors.yaml` says who the digest watches. A competitor listed there needs no
claims at all, which is the point: the most useful item in a digest is usually a
competitor nobody has written a comparison row about yet. Adding one is a copy-pasted
block with a dated source and `digest: true`.

**Group the digest by competitor, with a count in the summary line, and never truncate.**

```
<details><summary><strong>Greptile, 6 releases in the window</strong></summary>
- 2026-08-12 Linear integration ... `affects: no claim yet`
</details>
```

`<details>` renders natively in GitHub-flavoured markdown and in HTML, so one source
serves the repo report and a published page. The reader is tracking a competitor over
time, so a cap would throw away exactly what they came for. The count in the summary
line is itself the intel: "Greptile 6, CodeRabbit 1, Qodo 0" says something true about
the quarter, and **a competitor going quiet is information**, so name them and say zero.

Tiers control cost, not visibility. Tier 1 runs every time; tier 2 runs when the run has
room; tier 3 is claims only. If a tier-2 competitor is skipped, say so rather than
leaving a silent hole.

**Never invent a source URL.** A guessed changelog either 404s, which is loud and fine,
or returns a 200 shell, which reads as "they shipped nothing this week" and is the exact
silent failure this tool exists to prevent. Leave `url: null` with a `todo` and report
the competitor as untracked.

The two outputs answer different questions and both belong in a Monday message:

| Section | Question | Audience |
|---|---|---|
| Claim status | is anything we published now wrong | marketing, web |
| Shipped digest | what did our competitors do last week | sales, product, founders |

Digest rules:

- **Primary sources only.** Changelogs, release notes, dated blog posts, pricing pages.
  Not press coverage, not roundups, not another vendor's page about a competitor.
- **Every item gets a date and a link.** Same standard as a verdict.
- **Tag each item** as `affects a claim` (with the claim id), `competitive, no claim
  affected`, or `noise`. The middle bucket is the one that earns the digest its place:
  a competitor shipping a feature nobody has written a claim about yet is exactly what a
  sales team wants on Monday and what the claim file will need next quarter.
- **Say when a competitor shipped nothing.** Silence from a fast-moving competitor is
  information. Name them and say "no releases in the window."
- **Do not speculate.** Report what shipped. If a release implies a direction worth
  watching, put one line in Watch and label it as inference, not fact.
- **Cap it.** Ten items. If a week overflows, keep the ones affecting claims plus the
  most competitively significant, and say how many were left out. Never truncate
  silently.

Window defaults to 7 days, or to the date of the previous report if longer, so a skipped
week does not create a gap. State the window in the digest header.

### Slack shape

If the output is going to Slack rather than a file, the first line is the notification
preview, so it carries the verdict and the count. Then the digest, one line per item,
each with its link. Then a link to the full report. Three sections, no preamble, no
sign-off.

A quiet week in Slack is two lines. Resist making it longer.

## Tools

Fetching and diffing are mechanical and live in `tools/`. Rendering verdicts is not, and
stays with the agent.

```
python tools/crawl.py <target>                       # dated snapshot of the owner site
python tools/diff.py <target> <before> <after>       # sentence-level, MATERIAL vs REWORDING
python tools/published.py <target> <snapshot> --write  # resolve and persist published state
```

`crawl.py` exits non-zero when a required anchor is missing or the page count falls below
`floor_pages`. A run that cannot prove it fetched the site is a failure, never an
all-clear.

`diff.py` tags a change MATERIAL when it touches a number, a unit, a capability word or a
negation, and REWORDING otherwise. That heuristic ranks the work; it does not render the
verdict.

`published.py` declines to guess. Between roughly 0.35 and 0.70 match it returns
AMBIGUOUS rather than a state it cannot support, and the report carries the count.

## Adding a claim

Read the comparison page and add one entry per assertion. An assertion that no single
URL can settle is not a claim, it is marketing copy. Either find the source or mark it
`UNVERIFIABLE` and let the owner decide whether to keep publishing it.

Claims about your own product belong in the file too. The cheapest error to catch is a
comparison page that contradicts your own pricing page.

## What this skill does not do

- It does not edit the comparison pages. It reports; a human decides.
- It does not judge whether a competitor's product is good. It only asks whether a
  published sentence is still true.
- It does not scrape at volume. One weekly pass over 36 public URLs across 16 hosts. Respect
  robots.txt and do not add sources that require authentication.
