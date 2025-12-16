# Career History Knowledge Base Usage

This repository serves as a single source of truth for my career history, experiences, and skills. It is structured as a knowledge base that can be used to generate various formats of resumes and profiles.

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

- Python 3
- `pyyaml`
- `BasicTeX` (Optional, for PDF generation)

```bash
pip install pyyaml
brew install --cask basictex  # Optional
```

### Local Web "Command Center" (RECOMMENDED)

The easiest way to manage your resume is via the local web app, which provides a visual editor, AI tailoring, and live preview.

```bash
uv run uvicorn src.web.app:app --reload
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

**PDF Generation (New)**:
In the Web UI, click the **"Generate PDF (LaTeX)"** button to compile a high-quality PDF using the new LaTeX template. Requires `xelatex`.

### CLI Generation (Legacy)

To generate artifacts manually via CLI:

```bash
uv run python -m src.main [optional_jd_file]
```

### Adding New Data

Simply create a new YAML file in the corresponding directory under `data/`. The generator script automatically picks up all YAML files and sorts them by date.

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
