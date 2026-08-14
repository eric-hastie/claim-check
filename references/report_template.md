# Claim check: {{DATE}}

{{VERDICT_LINE}}
<!-- The first line is the whole report for most readers. Exactly one of:
     NOTHING TO REPORT. 23 claims checked, all current. No competitor releases this week.
     FYI ONLY. 2 competitor releases, no claim affected. Nothing to change.
     ACTION NEEDED: 2 claims. Greptile shipped an analytics dashboard (2026-04-15).
     No preamble, no restatement of the task, no padding on a quiet week. -->

## Action needed

<!-- OUT_OF_DATE first, ordered by traffic to the page carrying the claim. Omit the
     section entirely if empty, rather than writing "none". -->

### {{CLAIM_ID}} on {{PAGE}}

**Published:** "{{CLAIM_AS_WRITTEN}}"

**Out of date as of {{EVIDENCE_DATE}}** ({{WHAT_CHANGED}})
<!-- When evidence_date is "undated":
     "Out of date as of at least {{OBSERVED}}, no dated announcement located" -->

**See for yourself:** {{URL}}

**They say:** "{{EVIDENCE_QUOTE}}"

**Suggested edit:** {{REPLACEMENT_ROW_OR_DELETE}}

## Weakened

<!-- Still true, but the argument built on it no longer lands. Same date and link
     requirements. Say what the pitch was and what it should become. -->

## Unverifiable

<!-- Claims no source settles. These are the legal and credibility risk. Say what
     evidence would settle each one. -->

## Aging

<!-- CONFIRMED but not re-verified inside the aging window. Not findings. Listed so a
     quiet week is not mistaken for a verified week. -->

## What shipped {{WINDOW}}

<!-- Digest mode only (--digest). Everything competitors released in the window,
     whether or not it touches a claim. Primary sources only. Every item dated and
     linked. Name any tracked competitor that shipped nothing: silence from a fast
     mover is information. Cap at ten and say how many were left out. -->

| Date | Competitor | What shipped | Impact | Link |
|---|---|---|---|---|
| {{DATE}} | {{NAME}} | {{ONE_LINE}} | affects {{CLAIM_ID}} / competitive, no claim affected / noise | {{URL}} |

**No releases in the window:** {{COMPETITORS}}

## Watch

<!-- Not yet a finding. A competitor moving toward a capability a current claim depends
     on. Label inference as inference. -->

## Coverage

| Source | Pages | Result | Notes |
|---|---|---|---|
| {{URL}} | {{N}} | fetched / FAILED | {{reason if failed}} |

```
claims total {{N}} | selected {{N}} | verdicts returned {{N}} | sources attempted {{N}} | fetched {{N}} | failed {{N}}
```

{{FAILURE_NOTE}}
<!-- If any source failed, state plainly which claims went unverified as a result.
     A report that reads all-clear on a run with failed fetches is the failure mode
     this tool exists to prevent. -->
