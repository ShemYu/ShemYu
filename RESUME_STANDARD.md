# Resume publication standard

The YAML under `data/` is the source of truth. Canonical generation
(`uv run python -m src.main`) does **not** compose. It template-clips the
locked public `highlights` (newest roles, highlight caps in the concise HTML).

`--language ja` is the same clip path with localized labels and mapped
public strings. It does not call a model.

## Public vs evidence

Work and project `highlights` are the public layer (role, product,
disclosure-safe results). Put internal benchmarks, case counts, pp swings,
and similar eval notes in `evidence`.

`evidence` is the full archive. Constraint lines stay in YAML so humans know
what **not** to publish. They are not a license to put internal benchmarks
on the public page.

If a number or product name is missing from the publishable source, leave it
off the page. Do not guess.

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

Public / outbound coverage is **40% → 95% on a versioned eval set**.

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
