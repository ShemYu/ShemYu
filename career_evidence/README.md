# Career Evidence Workflow

This directory is the evidence layer upstream of the public resume data in `data/`.

The goal is to preserve enough detail to tailor a resume for different job descriptions without inventing facts, overstating causality, or losing the methodology behind a metric. Detailed masters may be long. Public resumes should be selective.

## Storage layers

| Layer | Location | Purpose |
|---|---|---|
| Detailed private master | `career_evidence/private/<company>.md` | Full product context, workstream history, metrics, denominators, versions, sources, boundaries, and interview gaps. Ignored by Git. |
| Private tailor-eval cases | `career_evidence/private/tailor_eval/cases/` | Real job descriptions and selection constraints scored against live `data/`. Ignored by Git with the rest of `private/`. |
| Publication data | `data/work/<company>.yaml` | Verified and disclosure-safe summary/highlights that generated resumes may publish. |
| Canonical outputs | `README.md`, `RESUME.md`, `output/resume*.html` | Generated artifacts. Never edit these to introduce a new career fact. |
| Tailored outputs | `output/tailored/` | Job-specific selections from publication data. They may shorten or reorder facts, never strengthen them. |

The current Cookpad master is `career_evidence/private/cookpad.md`. Its Obsidian copy is a research mirror; the repo-local file is the working source of truth.

## Private tailor-eval cases

Keep real job descriptions and their `must_*` / `preferred_*` constraints in `career_evidence/private/tailor_eval/cases/`. The parent `career_evidence/private/` directory is already in `.gitignore`; do not commit those files.

They are optional local fixtures for live tailor eval against publication YAML in `data/`. Copy a committed synthetic case from `tests/tailor_eval/cases/` as a template, then replace the JD and names with live `data/` work and project names. `--profile-dir data` on `python -m src.tailor_eval --live` overrides each case's `profile_dir`. See [USAGE.md](../USAGE.md) for the command.

**Open Question 3 (current role).** A tailored selection may drop the current role (Cookpad) when a JD matches an older role better. Recency is reported only; it is not a pass/fail gate. If Cookpad must appear, set `must_include_work: ["Cookpad"]` on that private case.

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
6. Regenerate canonical outputs with `uv run --locked python -m src.main`.
7. Tailor for a job description by selecting from canonical facts. Do not rewrite the evidence to match the job.

## Acceptance standard

A career bullet is ready for public data only when a reviewer can answer:

- What product or engineering problem did this solve?
- What did the person personally own?
- What changed, according to which compatible measurement?
- What was deployed, and to whom?
- What caveat would make the short wording misleading if omitted?

Unknown impact is acceptable. A detailed, honest evidence record is more useful than a complete-looking but unsupported bullet.
