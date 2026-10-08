# Resume publication standard

`career/` is the source of truth. Views under `views/` select claim ids and define the final document order. Canonical generation (`uv run python -m src.main`) is deterministic and does not call a model.

JD-tailored drafts follow [`skills/resume-tailoring/SKILL.md`](skills/resume-tailoring/SKILL.md). This file is the gate for the canonical pages. Do not apply or send a resume on the owner's behalf.

The one-pager may carry an editorial rewrite next to a selected claim id. The rewrite is presentation, not a new fact: it may shorten, normalize tense, or improve clarity, but every assertion must remain supported by the referenced public claim. A bullet may list `supporting_claims` when its implementation and outcome live on separate claim nodes. Every cited claim must be public, publishable, and attached to the same role (or the same project for project bullets).

Multi-claim bullets must provide an explicit rewrite for the current locale; the renderer never silently prints only the primary claim. The bound output records every source id in `highlight_claim_ids`, aligned one-to-one with `highlights`. Templates render every selected item exactly once and must not use hidden list slices, name-based filters, or language-specific content caps.

## Resume editorial standard

`views/one-pager.yaml` and `views/detailed.yaml` use `senior-impact-v1`. Approved bullets follow this order when the evidence supports it:

`ownership / implementation → operating context or problem → measurable outcome`

- A technology name is supporting detail, not the subject of the bullet.
- A benchmark or adoption number does not stand alone without the practice that produced or operationalized it.
- Implementation and outcome for the same system should normally be composed into one bullet.
- Filler openings such as “Responsible for” and “Worked on” are rejected.

The deterministic gate rejects obvious metric-first and tool-first regressions. Exact tests lock the approved wording. Neither mechanism permits an editorial rewrite to add facts beyond its cited claims; semantic accuracy still requires review when the wording changes.

The detailed resume is a separate English master artifact. It may span multiple pages and should include all substantive public claims without repeating the same result in both Experience and Technical Depth. Internal evidence stays excluded, and FinOps results from DOGI/FinOps are counted once.

`--language ja` is the same bind path with `text.ja` and view axis tags. It does not call a model.

## Public vs internal

`disclosure: public` claims may be listed on `views/one-pager.yaml`,
`views/detailed.yaml`, and `views/full.yaml`. Put internal benchmarks, case counts, pp swings, and
similar eval notes on `disclosure: internal` claims. The Bible view may
list them under evidence. The existing `do_not_claim` field stores scope notes
for later edits; explain those notes in neutral, specific language.

Use numbers and product names recorded on the referenced public pages.
When a detail is no longer clear from memory, use the broader description
that is still remembered and add a short detail-to-revisit note when useful.

## Project recollections and scope

Write retrospective project notes as professional recollections. State my
work and contributions directly. Keep estimates and open details beside
the relevant statement, using wording such as “I remember approximately…”
or “I no longer recall the exact…”. Preserve the distinction between my
work, team work, implemented behavior, and design proposals. Keep uncertainty
specific to the detail it concerns.

Use the skills, scale, proficiency, and experience duration recorded on the
source pages. Spark, TB-scale, QPS, TypeScript, LiteLLM, Unity Catalog, and
Delta remain outside the approved public wording. Total experience is
“6+ years”; the public wording excludes “7 years” and “7+ years”.

English level is Professional Working (owner decision 2026-09-28, replacing
Limited Working). Public wording is “English (Professional Working)”.

Cathay’s team scope is “Led 4 full-time engineers (7 including contractors)”.
DOGI’s contributor count describes a separate project team; the earlier
“10 cross-functional” and “coordinated 10” Cathay wording is outside this
team scope.

The Cathay RKB PoC was built jointly by Shem and a data scientist. Public
wording is “productionized the PoC”. Describe the PoC as joint work rather
than attributing its development solely to either person. I handled Databricks
production readiness. I no longer recall the exact data-layer product name,
so “Databricks data layer” preserves the level of detail I remember.

## Cookpad numbers

Public wording is **dish coverage 50% → 95%**; retain that metric name in
public copy. The 53/56 denominator stays on internal notes and is excluded
from the one-pager, detailed resume, and any other public page. The underlying
fixed 15-case, 56-item eval set is interview context. The earlier 40% result
used a different rubric, and 67.6 → 83.0 describes a separate evaluation
measure; neither is part of this dish-coverage comparison. The 67.6 → 83.0
measure is recorded separately from dish coverage and recall.

Supporting context kept outside the public resume:

- internal 67.6 → 83.0 (or +15.4 pp)
- 15-case / 103-unit or 56-case / 9 min
- flaky-miss RCA
- 20 users
- Moment team name (the product name “Moment Coach AI” appears on the detailed resume only). The Cookpad responsibility sentence stays on every resume, including one-pagers and platform-role variants. The one-pager uses the approved sentence without the product name; the detailed resume uses the approved sentence with it. Reuse these sentences from the [tailoring skill](skills/resume-tailoring/SKILL.md); the company slogan is outside the approved wording.

## Cathay F1 and RKB

F1 0.67 → 0.89 and RKB “adopted by 2 of 5 subsidiaries” describe the **same
system**. On the detailed resume they are separate bullets. A one-pager may
keep them as two independent sentences. The recorded facts describe both
quality improvement and adoption; the relationship between those outcomes
has not been established. Keep each outcome distinct in English and Japanese
wording rather than connecting them with causal phrases.
