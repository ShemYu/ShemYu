# Resume publication standard

`career/` is the source of truth. Views under `views/` select claim ids.
Canonical generation (`uv run python -m src.main`) does **not** compose.
It binds those ids and template-clips the one-pager.

`--language ja` is the same bind path with `text.ja` and view axis tags.
It does not call a model.

## Public vs internal

`disclosure: public` claims may be listed on `views/one-pager.yaml` and
`views/full.yaml`. Put internal benchmarks, case counts, pp swings, and
similar eval notes on `disclosure: internal` claims. The Bible view may
list them under evidence. `do_not_claim` stays on the node so humans know
what **not** to publish.

If a number or product name is missing from a public claim, leave it off
the page. Do not guess.

## Invented facts (never)

Do not invent Spark, TB-scale, QPS, TypeScript, LiteLLM, Unity Catalog, Delta,
“English Professional”, or “7 years”.

Do not write “10 cross-functional” for team size. Cathay’s team is 4 full-time
(7 including contractors). DOGI’s “10 contributors” is a different 10.

Do not write that Shem built the Cathay DS PoC. DS built the PoC; Shem did
Databricks production readiness.

Forgotten Databricks layer name: do not invent Unity Catalog or Delta. “Databricks
data layer” is the allowed wording.

## Cookpad numbers

Public / outbound coverage is **50% → 95% (53/56)** on a fixed 15-case,
56-item eval set. Do not write 40% → 95% as the same ruler.

Never put on the page:

- internal 67.6 → 83.0 (or +15.4 pp)
- 15-case / 103-unit or 56-case / 9 min
- flaky-miss RCA
- 20 users
- Moment team name

## Cathay F1 and RKB

F1 0.67 → 0.89 and RKB “adopted by 2 of 5 subsidiaries” describe the **same
system**. They may share one sentence.

Do **not** invent causality between them (no “F1 led to adoption”, “resulting
in adoption”, “because F1”, and no Japanese equivalents such as により採用 /
につながった).

Juxtaposition is allowed: “Improved regulatory Agent F1 from 0.67 to 0.89;
adopted by 2 of 5 subsidiaries.”
