# Resume Management

This repository uses the YAML files in `data/` as the single source of truth for the GitHub profile and resume.

## Structure

The data is organized in the `data/` directory:

- `data/basics.yaml`: Personal information and summary.
- `data/work/`: Work experiences (one YAML file per role).
- `data/education/`: Education history.
- `data/certificates/`: Certifications.
- `data/publications/`: Articles and publications.
- `data/skills/`: Skill sets by category.
- `data/projects/`: Significant projects.

## Usage

### Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)

### Update the Profile and Resume

1. Edit or add the relevant YAML file under `data/`.
2. Preview the generated files locally:

```bash
uv run python -m src.main
```

This updates:

- `README.md`: GitHub profile homepage.
- `RESUME.md`: Markdown resume.
- `output/resume.html`: One-page, ATS-friendly HTML resume for applications.
- `output/resume_bible.html`: Full HTML resume.

3. Commit and push the YAML changes. A push to `main` automatically regenerates and commits the profile and resume files.

The normal generation path is deterministic and does not require an AI API key.

### Tailor a Resume to a Job Description

Set `GEMINI_API_KEY` in `.env`, put the job description in a text file, and run:

```bash
uv run python -m src.main target_jd.txt
```

Tailored files are written under `output/` with the `_tailored` suffix. This is an opt-in local workflow and is not run by GitHub Actions.

### Adding New Data

Create a YAML file in the corresponding directory under `data/`. Work experience, education, and projects are automatically sorted by `startDate` in descending order.

For example, to add a new project, create `data/projects/my_new_project.yaml`:

```yaml
name: My New Project
description: Description of the project.
url: https://...
startDate: "2024-01"
endDate: "2024-06"
keywords:
  - Python
  - AI
highlights:
  - Achieved X result.
```

## Generated Resume

See [RESUME.md](./RESUME.md) for the latest generated version.
