# Sources

Which URL is authoritative for which kind of claim, and what a healthy fetch looks like.
Read before fetching. Update when a competitor moves a page.

## Fetch health

Every source lists an `anchor`: a string that must appear in the extracted text. If the
anchor is missing, the fetch FAILED even on a 200 response. This is what catches a
JavaScript shell or a redirect to a marketing splash. A 200 is not evidence that a page
loaded.

## Priority order

1. **Changelog.** Dated, specific, written by the vendor about themselves. Always
   preferred. It also catches the dangerous case: a competitor ships something and never
   updates the marketing page you are watching.
2. **Docs.** Precise on capability and limits. Rarely aspirational.
3. **Pricing.** Precise on money, and the place unit errors hide. Read the unit.
4. **Blog.** Good for strategy and stated intent. Weak evidence for capability.
5. **Marketing pages.** Last resort. Aspirational by construction.

Never use a third-party review site, a comparison blog, or another vendor's page about a
competitor as a primary source. Note that several high-ranking "best AI code review
tools" and "<competitor> alternatives" articles are published by vendors in this
category, including the owner of this file. Citing one of those to settle a claim is
circular.

## CodeRabbit

| Source | Settles | Anchor |
|---|---|---|
| https://www.coderabbit.ai/pricing | seat price, rate limits, multi-repo tiers, standalone security product, agent-minute billing | "per developer per hour" |
| https://docs.coderabbit.ai/guides/reports-overview | reporting and analytics | "Scheduled Reports" |
| https://docs.coderabbit.ai | capability, integrations, deployment | "CodeRabbit" |
| https://www.coderabbit.ai/blog | context architecture, CodeGraph, multi-repo analysis | "CodeRabbit" |

Watch: the rate limit unit is per developer **per hour**, not per month. This is the
single most consequential number on the page.

## Greptile

| Source | Settles | Anchor |
|---|---|---|
| https://www.greptile.com/changelog | everything shipped, with dates | "Greptile v" |
| https://www.greptile.com/pricing | seat price, credits, free tier, startup discount | "per seat" |
| https://www.greptile.com/docs/code-review-bot/billing-seats | credit mechanics, flex usage caps | "flex usage" |
| https://www.greptile.com/docs/analytics | analytics dashboard scope | "Analytics Dashboard" |
| https://www.greptile.com/docs/code-review/key-features | capability surface, TREX, MCP, auto-approve | "Full codebase context" |
| https://www.greptile.com/docs/deployment-options | self-hosting, SCM support, licensing | "Self-Hosted" |
| https://www.greptile.com/agent-leaderboard | AI authorship and agent quality metrics they publish | "Agent leaderboard" |
| https://www.greptile.com/blog | strategy and stated refusals | "Greptile" |

Watch: they ship fast. Six competitively relevant features landed between 2026-04-15 and
2026-08-05. The changelog is the highest-yield single URL in this file.

## Self

| Source | Settles | Anchor |
|---|---|---|
| https://getoptimal.ai/pricing | own tiers, review caps, what happens past the cap | "deep PR reviews per user per month" |
| https://getoptimal.ai/vs | the claims themselves | "Optibot vs" |

Check own pages every run. A comparison page that contradicts your own pricing page is
the cheapest error in the file to find and the most expensive to leave up.

## Qodo Merge

| Source | Settles | Anchor | Verified |
|---|---|---|---|
| https://qodo.ai/pricing/ | plan prices, credit metering, analytics | "credit" | 2026-08-12 |
| https://qodo-merge-docs.qodo.ai/core-abilities/rag_context_enrichment/ | context scope, RAG, /implement | "RAG context enrichment" | 2026-08-14 |
| https://docs.qodo.ai/changelog | releases | "chronological record of changes to Qodo" | 2026-08-14 |

Watch: RAG context is documented as enterprise plan only, single tenant or on-prem. Any
context claim has to say which tier it applies to.

## SonarQube

| Source | Settles | Anchor | Verified |
|---|---|---|---|
| https://www.sonarsource.com/plans-and-pricing/ | pricing model (per instance, per LOC) | "lines of code" | 2026-08-14 |
| https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/pull-request-analysis | PR decoration and inline annotations | "pull request" | 2026-08-14 |
| https://docs.sonarsource.com/sonarqube-server/2026.1/ai-capabilities/ai-codefix | AI CodeFix, AI Code Assurance | "AI CodeFix" | 2026-08-14 |

Watch: Sonar prices per instance per year by lines of code, never per developer. Any
per-seat comparison against Sonar is wrong before the number is.

## DeepSource

| Source | Settles | Anchor | Verified |
|---|---|---|---|
| https://deepsource.com/pricing | plans, Autofix, AI review, coverage | "Autofix" | 2026-08-14 |

Watch: Autofix is long-standing and unlimited on Team and Enterprise. Any "no auto-fix"
claim about DeepSource fails on their pricing page.

## GitHub Copilot

| Source | Settles | Anchor | Verified |
|---|---|---|---|
| https://github.com/features/copilot/plans | plan prices, what code review includes, credit consumption | "code review" | 2026-08-14 |
| https://docs.github.com/en/copilot/using-github-copilot/code-review/using-copilot-code-review | how review runs, context, instructions | "Copilot code review" | 2026-08-14 |
| https://github.blog/changelog/label/copilot/ | dated releases | "Copilot" | 2026-08-14 |

Watch: plans move often. As of 2026-08-14 they are Free $0, Pro $10, Pro+ $39, Max $100,
with code review included on paid plans, consuming GitHub AI Credits and, since
2026-06-01, GitHub Actions minutes.

## Digest-only competitors

These carry no claims. They are watched so the Monday digest reflects the field, not
only the vendors already named on a comparison page. Full entries in
`competitors.yaml`.

| Source | Settles | Anchor | Verified |
|---|---|---|---|
| https://cursor.com/changelog | Bugbot pricing and review changes | "Changelog" | 2026-08-14 |
| https://code.claude.com/docs/en/changelog | native review, subagents, agent pricing | "Claude Code" | 2026-08-14 |
| https://github.blog/changelog/label/copilot/ | Copilot code review releases, dated and filterable | "Copilot" | 2026-08-14 |
| https://docs.qodo.ai/changelog | Qodo releases | "chronological record of changes to Qodo" | 2026-08-14 |
| https://graphite.com/blog | Graphite Agent releases (no changelog feed exists) | "Graphite" | unverified |

Two gaps worth stating in every report rather than leaving silent:

- **CodeRabbit publishes no dated changelog feed** that we could locate. Their changes
  arrive through pricing and docs diffs, which means late. A quiet CodeRabbit week in
  the digest means "not detected," not "nothing shipped."
- **Graphite has no changelog feed either.** Changelog posts go on the blog, and
  `/docs/cli-changelog` covers only the CLI. Also note the rename: Diamond was folded
  into Graphite Agent on 2025-10-08, so any claim naming Diamond is already stale.

## Adding a competitor

Add the changelog and the pricing page first. Those two settle most claims. Add docs
pages only for claims that pricing and changelog cannot settle. Resist adding marketing
pages: they generate diff noise and rarely settle anything.

Everything on the comparison pages is now tracked, plus Cursor Bugbot, Claude Code,
Graphite, Augment and Cubic for the digest. Two still need a dated release feed located
before they can join the digest: Augment and Cubic. Do not guess either URL.
