# Resume sentence standard

First draft. Iterate sentence taste locally; do not treat this file as career
history. The YAML under `data/` remains the source of truth. Tailoring may
compose at most three resume-standard sentences per selected role from that
role's facts. It must not invent experience.

Canonical generation (`uv run python -m src.main`, no job description) does
**not** compose. It template-clips the locked public `highlights` (newest
roles, highlight caps in the concise HTML). Compose runs only when a JD is
supplied.

## Sentence shape

- One idea per line.
- Verb + scope + result.
- At most three lines per selected work or project role.
- Prefer production, measurement, and ownership that the JD actually needs.

## Grounding (hard fail)

Every number, proper name, and causal claim on the page must already appear in
that role's **publishable** source:

- locked public `highlights`
- `evidence` lines that are not tagged do-not-claim / not outbound /
  evidence-only / do-not-invent

`evidence` is the full archive. Constraint lines stay in YAML so the composer
knows what **not** to write. They are not a license to publish internal
benchmarks.

If a number or product name is missing from the publishable source, drop it.
Do not guess.

## Do not write unless the JD needs them

- Awards, MVP titles
- Generic “deployed on X ensuring scalable and secure operations”
- Documentation-only / onboarding-docs bullets

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

Public / outbound coverage is **50% → 95% (53/56) on a fixed 15-case, 56-item eval set**.

Do not write **40% → 95%** as the public sentence. That earlier shorthand used a different ruler (30/74 = 40.5%).

Never put on the page:

- internal 67.6 → 83.0 (or +15.4 pp)
- 103-unit
- 56-case / 9 min
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
