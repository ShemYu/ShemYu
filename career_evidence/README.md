# Career Evidence Workflow

This directory is the evidence layer upstream of the public resume data in `data/`.

The goal is to preserve enough detail to support a public resume without inventing facts, overstating causality, or losing the methodology behind a metric. Detailed masters may be long. Public resumes should be selective.

## Storage layers

| Layer | Location | Purpose |
|---|---|---|
| Detailed private master | `career_evidence/private/<company>.md` | Full product context, workstream history, metrics, denominators, versions, sources, boundaries, and interview gaps. Ignored by Git. |
| Tracked Git-history inventory | `career_evidence/moment_coach_ai_git_history.md` | Main-branch contribution ledger and resume-use boundaries derived from Moment Coach AI commits. |
| Publication data | `data/work/<company>.yaml` | Verified and disclosure-safe summary/highlights that generated resumes may publish. |
| Canonical outputs | `README.md`, `RESUME.md`, `output/resume*.html` | Generated artifacts. Never edit these to introduce a new career fact. |

The current Cookpad master is `career_evidence/private/cookpad.md`. Its Obsidian copy is a research mirror; the repo-local file is the working source of truth.

## Evidence states

Use explicit status labels in a private master:

- `[Repo verified]`: reproduced or traced to repository code, commits, reports, or run artifacts.
- `[User confirmed]`: confirmed by the owner in an interview but not independently located in local artifacts.
- `[Derived]`: arithmetic calculated from verified inputs; retain the formula or numerator/denominator.
- `[Interview needed]`: materially affects scope or impact and cannot be inferred safely.
- `[Do not claim]`: unsupported, incompatible, confidential, or likely to mislead.

## Required boundaries

Before promoting a claim into `data/`, check:

1. **Time:** separate employment dates, workstream evidence dates, and experiment/report dates.
2. **Ownership:** distinguish personal design/implementation/decision ownership from team infrastructure or shared delivery.
3. **Release state:** distinguish prototype, internal evaluation, merged code, production deployment, product launch, and measured live traffic.
4. **Metric contract:** retain metric definition, numerator/denominator, case count, cohort, run versus union, evaluator/extractor version, date, and material cost tradeoffs.
5. **Comparability:** do not connect incompatible cohorts or instruments into a single improvement curve.
6. **Attribution:** do not assign a bundled generation/schema/extraction/judge improvement to one prompt or component without a controlled comparison.
7. **Disclosure:** keep internal paths, incident identifiers, unpublished business context, and uncertain claims out of public YAML unless explicitly approved.

## Workflow

1. Capture the detailed evidence and limitations in the private company master.
2. Search local sources before asking the owner; list only the questions that files cannot answer.
3. Resolve timeline, ownership, deployment, and impact gaps through interview.
4. Draft several source-faithful bullet candidates in the private master.
5. Promote verified, disclosure-safe facts into `data/work/<company>.yaml`.
6. Regenerate canonical outputs with `uv run --locked python -m src.main`. Do not rewrite evidence to match a job description.

## Acceptance standard

A career bullet is ready for public data only when a reviewer can answer:

- What product or engineering problem did this solve?
- What did the person personally own?
- What changed, according to which compatible measurement?
- What was deployed, and to whom?
- What caveat would make the short wording misleading if omitted?

Unknown impact is acceptable. A detailed, honest evidence record is more useful than a complete-looking but unsupported bullet.
