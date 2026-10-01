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
list them under evidence. `do_not_claim` stays on the node so humans know
what **not** to publish.

If a number or product name is missing from a public claim, leave it off
the page. Do not guess.

## Invented facts (never)

Do not invent Spark, TB-scale, QPS, TypeScript, LiteLLM, Unity Catalog, Delta,
or “7 years” / “7+ years”. Total experience is “6+ years”.

English level is Professional Working (owner decision 2026-09-28, replacing
Limited Working). Public wording is “English (Professional Working)”.

Do not write “10 cross-functional” or “coordinated 10” for team size. Cathay’s
team is “Led 4 full-time engineers (7 including contractors)”. DOGI’s contributor
count is a different internal note, not the team size.

The Cathay RKB PoC was built jointly by Shem and a data scientist. Public
wording is “productionized the PoC”. Do not write “DS built the PoC” or “the
data scientist's PoC”, and do not imply Shem built it alone.

Forgotten Databricks layer name: do not invent Unity Catalog or Delta. “Databricks
data layer” is the allowed wording.

## Cookpad numbers

Public wording is **dish coverage 50% → 95%**. Never call that result recall.
The 53/56 denominator stays on internal notes, not on the one-pager, the
detailed resume, or any other public page. The underlying fixed 15-case,
56-item eval set is interview context. Do not write 40% → 95% as the same
ruler. Do not treat 67.6 → 83.0 as dish coverage, as recall, or as a second
coverage curve.

Never put on the page:

- internal 67.6 → 83.0 (or +15.4 pp)
- 15-case / 103-unit or 56-case / 9 min
- flaky-miss RCA
- 20 users
- Moment team name (the product name “Moment Coach AI” appears on the detailed resume only; never on the one-pager). The one-pager keeps the same Cookpad responsibility sentence without the product name; see the tailoring skill. Do not substitute the company slogan.

## Cathay F1 and RKB

F1 0.67 → 0.89 and RKB “adopted by 2 of 5 subsidiaries” describe the **same
system**, not a causal pair. On the detailed resume they are separate bullets.
A one-pager may keep them as two independent sentences. Do **not** invent
causality (no “F1 led to adoption”, “resulting in adoption”, “because F1”,
and no Japanese equivalents such as により採用 / につながった).
