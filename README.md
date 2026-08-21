# claim-check

A Claude skill that keeps competitor comparison pages true.

Every source it reads is a public vendor page: changelogs, pricing pages, product docs.
Every finding carries the date it went stale and a link, so anyone can check it in one
click. Nothing here is scraped from behind a login, and nothing is inferred.

**Point it at your own site.** Copy `targets/example/`, fill in your comparison pages
and the claims they make, and the weekly run tells you which ones a competitor has
already invalidated. Targets can live outside this repo entirely, via
`CLAIM_CHECK_TARGETS`, so findings about a real company stay private while the tool
stays shareable.

Comparison pages are high-intent inbound: someone typing "X vs Y" is evaluating right
now, and the page is the only rep in the room. They are also the fastest-rotting content
a company publishes, because a competitor can ship on Tuesday and nobody updates the
table. In AI code review, six competitively relevant features shipped across a single
competitor between April and August 2026.

This skill re-checks each published claim against the primary source that would settle
it, weekly, and reports only what changed.

## What makes it different from a page monitor

It watches claims, not pages. A page monitor tells you a competitor's pricing page
changed, which is usually a testimonial rotation. It cannot tell you that a competitor
shipped a feature that makes row four of your comparison table out of date without ever
touching the page you watch. Claims are the unit, and each claim names the source that
settles it.

## Install

**Claude Code:** copy this directory into `.claude/skills/claim-check/`, then run
`/claim-check`.

**claude.ai or anything else:** use `dist/claim-check-standalone.md`. It is the same
content in one self-contained file, suitable as a project instruction or a paste. Run
`python3 build_standalone.py` to regenerate it after editing.

## Use

```
/claim-check                       # full weekly run
/claim-check --digest              # adds "what competitors shipped last week"
/claim-check greptile              # one competitor
/claim-check --claim gt-no-analytics
```

Output is a dated file in `reports/`, plus an updated `claims.yaml`. Commit both. Git
history becomes the audit trail: when a claim went stale, what the evidence was, and
when it was fixed.

## Two outputs, one run

| Section | Question it answers | Who reads it |
|---|---|---|
| Claim status | is anything we published now out of date | marketing, web |
| What shipped (`--digest`) | what did our competitors actually do last week | sales, product, founders |

The digest is close to free, since the changelogs are already being fetched to check the
claims. It is also the part people open on a Monday, which is what keeps the habit
alive. Items are tagged `affects a claim`, `competitive, no claim affected`, or `noise`,
and a tracked competitor that shipped nothing gets named, because silence from a fast
mover is information.

## The first line is a verdict

Every report opens with exactly one of these, and nothing else:

```
NOTHING TO REPORT. 23 claims checked, all current. No competitor releases this week.
FYI ONLY. 2 competitor releases, no claim affected. Nothing to change.
ACTION NEEDED: 2 claims. Greptile shipped an analytics dashboard (2026-04-15).
```

That line is the Slack notification preview, so it has to carry the whole verdict. A
quiet week is two lines and should stay two lines: padding a nothing week to look
productive is how a weekly report gets muted, and a muted report is worse than none.

## Every finding is dated and linked

No finding says "this is wrong." It says when it went out of date, what changed on that
date, and where to look:

```
Out of date as of 2026-04-15 (Greptile changelog: analytics dashboard)
See for yourself: https://www.greptile.com/docs/analytics
They say: "Track code review metrics across your organization: PRs reviewed,
merge times, addressed rates, critical bugs caught..."
```

When a vendor publishes no date, the report says "out of date as of at least
<first-observed>, no dated announcement located." An observation date is never presented
as a release date.

Each finding also carries a `cause`, because the three kinds get fixed differently:
`competitor_shipped` (a dated release changed the facts), `source_check` (the current
source does not support the claim, with no release to point at), and `internal_conflict`
(one of your own pages says something different).

## Adding a competitor

Copy a block in `competitors.yaml`, point it at a dated release feed, set `digest: true`.
No claims required: the digest and the claim check are independent, and a competitor
nobody has written a comparison row about is often the one worth reading about on Monday.

Tier 1 runs every time, tier 2 runs when there is room and gets dropped first, tier 3 is
claims only. If a tier-2 competitor is skipped, the report says so.

One rule: never guess the changelog URL. A wrong one either 404s, which is loud and
fine, or returns an empty 200 that reads as "they shipped nothing." Leave it null with a
`todo` until you have confirmed it loads.

## Running it weekly

The skill is the process; something has to fire it. Any of these works:

- A scheduled Claude Code cloud agent, weekly, with the report posted to Slack.
- A GitHub Action on a cron that runs the skill and opens a pull request titled
  "3 claims need review."
- A calendar reminder and a person. This is fine. The run takes a few minutes.

The pull request version is the one worth aiming at: marketing reviews a diff on Monday,
edits the page or dismisses the finding, and the state file records the decision.

## Files

| File | What it is |
|---|---|
| `SKILL.md` | The process: select, fetch, verdict, update state, report, reconcile |
| `claims.yaml` | Every published claim, its sources, current verdict and evidence. Input and state |
| `competitors.yaml` | Who the digest watches, in tiers, with a dated source and anchor each |
| `references/sources.md` | Which URL settles which kind of claim, per competitor, with fetch-health anchors |
| `references/report_template.md` | Report shape |
| `reports/` | Dated output |
| `build_standalone.py` | Concatenates the above into the single-file paste version |

## Design decisions worth keeping

**Four verdicts, not two.** CONFIRMED, WEAKENED, OUT_OF_DATE, UNVERIFIABLE. Most real
movement is "weakened": a competitor adds a spend cap, which does not make
"usage-based pricing" untrue but does kill the pitch built on unpredictable bills. A
true/false system reports nothing on the week that matters most.

**Fail loudly.** A 200 response is not evidence that a page loaded. Every source carries
an anchor string that must appear in the extracted text, and a run with failed fetches
cannot produce an all-clear report. A monitor that quietly reports "no changes" when it
is broken is worse than no monitor.

**Reconcile the counts.** Every run ends with claims selected, verdicts returned,
sources attempted, fetched and failed. If verdicts returned is lower than claims
selected, the missing ones get named. Silent shrinkage between those numbers is the
failure this tool exists to prevent.

**Your own claims are in the file.** The cheapest error to catch is a comparison page
that contradicts your own pricing page.

**Silence is not support.** If the sources load and say nothing about a claim, the
verdict is UNVERIFIABLE, never CONFIRMED. Competitor claims about compliance and
security carry real exposure when nothing backs them.

## Seed data

`claims.yaml` ships populated with 23 real claims from three live comparison pages, and
`reports/2026-08-14.md` is the baseline run. It is not a template with placeholder rows:
9 of the 23 are out of date, each with the date it went stale and a link to the evidence.

## Etiquette

One weekly pass over roughly 20 public URLs. Respect robots.txt, do not add
authenticated sources, and do not scrape at volume. The vendor changelog is public
because vendors want it read.
