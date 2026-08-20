# Resume Management

The YAML files under `data/` are the single source of truth for the GitHub profile and resumes. Every load is checked against the shared profile schema before a template or AI agent can use the data.

## Evidence-first content standard

Treat the canonical YAML as the publication layer, not as a place to invent or inflate career facts. Keep a detailed, source-backed evidence record upstream when an experience needs more context than a resume can carry, then promote only verified claims into `data/`.

- Capture detail before compression: product problem, personal contribution, outcome, dates, denominator, cohort, metric definition, evaluator or system version, and important limitations.
- Keep employment dates, project or evidence windows, and individual experiment windows separate.
- Distinguish repository-verified facts, user-confirmed context, derived calculations, unresolved interview fields, and claims that must not be made.
- Do not join incompatible cohorts, single runs, multi-run unions, evaluator versions, or release states into one improvement curve.
- Do not translate an internal benchmark or production deployment into customer adoption, live-traffic impact, or an online A/B result without matching evidence.
- Leave unknown impact numbers out of public YAML until the user can substantiate them; never estimate a resume metric merely to complete a bullet.
- Tailoring may select, shorten, and reorder source facts for a job description. It must not strengthen causality, change scope, or add facts absent from the canonical data.

The full or Bible output may remain detailed. Concise and job-specific outputs are downstream selections from the same evidence, not separate versions of truth.

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

The concise HTML includes the three newest roles, up to three highlights per role, and up to seven keywords per technical skill group. Use the Bible HTML or Markdown resume when you need the complete source-backed history.

Commit the YAML changes and all four canonical files together. The main GitHub Actions workflow validates pull requests without write access. After a push to `main`, it regenerates them as a drift backstop in a read-only job; only a separate commit job can write a missing correction.

The normal generation path is deterministic and does not load an AI provider or require an API key. Invalid fields, malformed dates, unknown schema fields, and unsafe URL schemes fail with a source-aware validation error.

## Tailor a resume to a job description

Copy the environment template and place your own key in the ignored `.env` file:

```bash
cp .env.example .env
```

```dotenv
TAILOR_PROVIDER=openai
OPENAI_API_KEY=your-key-here
# Optional; defaults to gpt-5.6-luna
OPENAI_MODEL=gpt-5.6-luna
XAI_API_KEY=your-xai-key-here
# Optional; defaults to grok-4.6
XAI_MODEL=grok-4.6
```

`build_provider()` selects the backend from `--provider`, then `TAILOR_PROVIDER`, then `openai`. OpenAI is the default. `--provider` and `--model` are only valid with a job-description file; `--model` overrides `OPENAI_MODEL` or `XAI_MODEL` for the selected provider.

Save a job description as `target_jd.txt` (an ignored local file), then run:

```bash
uv run --locked --extra tailoring python -m src.main target_jd.txt
```

To label the ignored output files for a particular role, or to pin provider and model:

```bash
uv run --locked --extra tailoring python -m src.main target_jd.txt --output-name cookpad_ai
uv run --locked --extra tailoring python -m src.main target_jd.txt --provider openai --model gpt-5.6-luna
```

To tailor with xAI (`grok-4.6`) instead of OpenAI, pass `--provider xai`. The CLI default stays OpenAI.

```bash
uv run --locked --extra tailoring python -m src.main target_jd.txt --provider xai --output-name cookpad_ai
```

This writes `output/tailored/cookpad_ai.md`, `output/tailored/cookpad_ai.html`, and `output/tailored/cookpad_ai_bible.html`. Keeping tailored files in their own ignored directory prevents a job-specific basename from overwriting canonical artifacts. The provider returns only a structured selection of source indices; the local assembler copies the selected facts and bullet points from the validated profile. It cannot rewrite or add career facts. Work and project `evidence` is stripped from the model prompt, so internal eval notes are not sent; the assembler still copies them for the Bible output.

For GitHub Actions, create a repository Actions secret named `OPENAI_API_KEY`, then run **Tailor Resume with OpenAI** manually and download its artifact. This workflow is read-only, does not commit job-specific resumes, and is the only workflow that receives the secret. The job description is a plain workflow input, so use the local command instead when a job description is confidential.

## Check tailoring faithfulness (offline)

Pull-request CI is `unittest` only. The core job runs `tests.test_tailor_eval` with no API keys and no `tailoring` extra. Those tests assemble a hand-written plan, render the real templates, and scan public MD/HTML for source-faithful strings.

`python -m src.tailor_eval` is validate-only: it loads case YAML and resolves `must_*` / `preferred_*` names. It does not assemble, render, or call a provider.

```bash
uv run --locked python -m unittest tests.test_tailor_eval -v
uv run --locked python -m src.tailor_eval
```

## Check tailoring stability (live)

`python -m src.tailor_eval --live` is opt-in. It is not pull-request CI and requires the selected provider's API key (`XAI_API_KEY` for `--provider xai`, `OPENAI_API_KEY` for OpenAI).

Each case is repeated N times (default 5, min 3, max 9). Public and Bible templates render in a temporary directory, not canonical files. A JSON report is written under `output/tailor_eval/{case_id}-{provider}-{timestamp}.json`.

A live case passes when every repeat produces a valid plan and assemble, scanners have no fail findings, and mean pairwise Jaccard on selected work and project names is at least 0.60. Preferred-set recall, keyword coverage, recency, and role match are reported, not gated. Reasoning-token usage and wall time are recorded as data, not pass/fail targets.

```bash
uv run --locked --extra tailoring python -m src.tailor_eval --live --provider xai
uv run --locked --extra tailoring python -m src.tailor_eval --live \
    --provider xai --repeats 5 \
    --cases tests/tailor_eval/cases
uv run --locked --extra tailoring python -m src.tailor_eval --live \
    --provider xai --profile-dir data \
    --cases career_evidence/private/tailor_eval/cases
```

Exit 0 if every live case passed, 1 if a case failed the gates or a case YAML/name is invalid, 2 if configuration is missing (unknown `--provider`, missing API key, missing `--cases` directory, or `--repeats` outside 3–9).

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
