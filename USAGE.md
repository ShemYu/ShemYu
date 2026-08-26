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
- Tailoring may select roles and compose at most three resume-standard sentences per selected role from that role's publishable facts. It must not strengthen causality, change scope, or add facts absent from the canonical data. See [`RESUME_STANDARD.md`](RESUME_STANDARD.md).

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

The concise HTML includes the three newest roles, up to three highlights per role, and up to seven keywords per technical skill group. This no-JD path is **template clip**: it does not call a model and does not compose new sentences. Use the Bible HTML or Markdown resume when you need the complete source-backed history.

Commit the YAML changes and all four canonical files together. The main GitHub Actions workflow validates pull requests without write access. After a push to `main`, it regenerates them as a drift backstop in a read-only job; only a separate commit job can write a missing correction.

The normal generation path is deterministic and does not load an AI provider or require an API key. Invalid fields, malformed dates, unknown schema fields, and unsafe URL schemes fail with a source-aware validation error.

## Tailor a resume to a job description

Copy the environment template and place your own key in the ignored `.env` file:

```bash
cp .env.example .env
```

```dotenv
OPENAI_API_KEY=your-key-here
# Optional; defaults to gpt-5.6-luna
OPENAI_MODEL=gpt-5.6-luna
```

Save a job description as `target_jd.txt` (an ignored local file), then run:

```bash
uv run --locked --extra tailoring python -m src.main target_jd.txt
```

To label the ignored output files for a particular role:

```bash
uv run --locked --extra tailoring python -m src.main target_jd.txt --output-name cookpad_ai
```

To emit a one-page Japanese 職務経歴書 from the same concise tailor harness (`resume.html.j2`, not a second template pipeline):

```bash
uv run --locked --extra tailoring python -m src.main target_jd.txt --language ja --output-name ly_platform_jp
```

`--language` defaults to `en`. The agent selects roles / projects / skills / certs / pubs by index and **composes** at most three grounded bullets per selected work or project role. Compose in the target language (`en` or `ja`), then `src/i18n.py` translates remaining assembled strings (section labels, titles, mapped public highlights). Language lines come only from `data/skills/language.yaml` (中国語（母語） / 英語（限定的な実務）). The header may show `余顯漁（Shem Yu）` as a documented display alias; the Chinese characters are not stored in `basics.yaml`. After HTML is written, the job renders a PDF and **fails if the page count is not exactly 1**.

A local grounding checker hard-fails the run if a composed bullet invents a number, product/layer name (Unity Catalog, Delta, Spark / TB / QPS), F1→adoption causality, or a do-not-claim internal metric (Cookpad 67.6→83, flaky, 20 users).

English tailored files are written as `output/tailored/<name>.md`, `.html`, and `_bible.html`. `--language ja` uses those same paths and also writes a sibling `.pdf` after the one-page check. Keeping tailored files in their own ignored directory prevents a job-specific basename from overwriting canonical artifacts.

## Review composed sentences locally

Cloud / CI does not need `OPENAI_API_KEY`. Grounding and tailor-eval compose cases are offline.

To review **sentence taste** with your own key:

```bash
uv run --locked --extra tailoring python -m src.main target_jd.txt --output-name review_en
uv run --locked --extra tailoring python -m src.main target_jd.txt --language ja --output-name review_ja
```

Optional live-model smoke (skipped when the key is missing; do not add this to CI):

```bash
# Requires OPENAI_API_KEY in .env
uv run --locked --extra tailoring python -m src.main target_jd.txt --language en --output-name live_smoke
```

Iterate `RESUME_STANDARD.md` and re-run. Do not edit `data/` to invent experience.

For GitHub Actions, add a repository Actions secret named `OPENAI_API_KEY`, then run **Tailor Resume with OpenAI** manually and download its artifact. The workflow fails immediately if that secret is empty. It is read-only and does not commit job-specific resumes. The job description is a plain workflow input, so use the local command instead when a job description is confidential.

## Check tailoring faithfulness (offline)

Pull-request CI is `unittest` only. The core job runs `tests.test_tailor_eval` with no API keys and no `tailoring` extra. Those tests assemble a hand-written pick or compose plan, render the real templates, and scan public MD/HTML for grounded / source-faithful strings.

`python -m src.tailor_eval` is validate-only: it loads case YAML and resolves `must_*` / `preferred_*` names. It does not assemble, render, or call a provider.

```bash
uv run --locked python -m unittest tests.test_tailor_eval tests.test_grounding -v
uv run --locked python -m src.tailor_eval
```

The tailor-eval suite includes an offline `--language ja` check: a hand-written plan is assembled, localized, and rendered through `resume.html.j2`. It asserts Japanese headings, unchanged source numbers, no invented Japanese fluency or LiteLLM, and documents the one-page PDF gate (`assert_one_page`). That path does not call the OpenAI API.

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
