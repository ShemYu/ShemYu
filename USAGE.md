# Resume Management

The YAML files under `data/` are the single source of truth for the GitHub profile and resumes. Every load is checked against the shared profile schema before a template can use the data.

## Evidence-first content standard

Treat the canonical YAML as the publication layer, not as a place to invent or inflate career facts. Keep a detailed, source-backed evidence record upstream when an experience needs more context than a resume can carry, then promote only verified claims into `data/`.

- Capture detail before compression: product problem, personal contribution, outcome, dates, denominator, cohort, metric definition, evaluator or system version, and important limitations.
- Keep employment dates, project or evidence windows, and individual experiment windows separate.
- Distinguish repository-verified facts, user-confirmed context, derived calculations, unresolved interview fields, and claims that must not be made.
- Do not join incompatible cohorts, single runs, multi-run unions, evaluator versions, or release states into one improvement curve.
- Do not translate an internal benchmark or production deployment into customer adoption, live-traffic impact, or an online A/B result without matching evidence.
- Leave unknown impact numbers out of public YAML until the user can substantiate them; never estimate a resume metric merely to complete a bullet.

See [`RESUME_STANDARD.md`](RESUME_STANDARD.md) for public-vs-evidence rules and claims that must not appear on the page.

The full or Bible output may remain detailed. The concise one-pager is a downstream clip of the same locked public highlights, not a separate version of truth.

Work and project `highlights` are the public layer (role, product, disclosure-safe results). Put internal benchmarks, case counts, pp swings, and similar eval notes in `evidence`. The generator strips `evidence` from `resume.html`, `RESUME.md`, and `README.md`; the Bible template can still show it.

Repository-local evidence guidance lives in [`career_evidence/README.md`](career_evidence/README.md). Detailed company masters belong under `career_evidence/private/`, which is intentionally ignored so internal context cannot enter the public profile by accident. Promote only disclosure-safe, verified wording from a private master into `data/`.

## Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)

Install the exact locked dependencies:

```bash
uv sync --locked
```

## Update the canonical resume

1. Edit or add YAML under `data/`.
2. Generate all canonical files as one atomic batch:

```bash
uv run --locked python -m src.main
```

The command updates these files only after every template renders successfully:

- `README.md`: GitHub profile homepage
- `RESUME.md`: public Markdown resume
- `output/resume.html`: concise A4 HTML resume
- `output/resume_bible.html`: full HTML resume

The concise HTML includes the three newest roles, up to three highlights per role, and up to seven keywords per technical skill group. This path is **template clip**: it does not call a model and does not compose new sentences. Use the Bible HTML or Markdown resume when you need the complete source-backed history.

Commit the YAML changes and all four canonical files together. The main GitHub Actions workflow validates pull requests without write access. After a push to `main`, it regenerates them as a drift backstop in a read-only job; only a separate commit job can write a missing correction.

Generation is deterministic and does not load a model or require an API key. Invalid fields, malformed dates, unknown schema fields, and unsafe URL schemes fail with a source-aware validation error.

## Render a Japanese 職務経歴書

`--language ja` is the same deterministic clip path, not a second generator. It localizes locked public highlights through `src/i18n.py` (section labels, titles, mapped public strings) and writes the same canonical artifacts. Language lines come only from `data/skills/language.yaml` (中国語（母語） / 英語（限定的な実務）). The header may show `余顯漁（Shem Yu）` as a documented display alias; the Chinese characters are not stored in `basics.yaml`. After HTML is written, the job renders `output/resume.pdf` and **fails if the page count is not exactly 1**.

```bash
uv run --locked python -m src.main --language ja
```

`--language` defaults to `en`. Japanese rendering does not compose new sentences.

## Add structured data

Create one YAML file per entry in the corresponding directory:

- `data/basics.yaml`
- `data/work/`
- `data/education/`
- `data/certificates/`
- `data/publications/`
- `data/skills/`
- `data/projects/`

Work, education, and projects are sorted by normalized `startDate` in descending order. Use `YYYY`, `YYYY-MM`, or `YYYY-MM-DD`; use `Present` only as an end date.

Example project:

```yaml
name: My New Project
description: Description of the project.
url: https://example.com/project
startDate: "2024-01"
endDate: "2024-06"
keywords:
  - Python
  - AI
highlights:
  - Achieved a measured result.
```

See [RESUME.md](./RESUME.md) for the latest generated Markdown resume.
