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

```bash
pip install pyyaml
```

### Generate Resume

To generate the `RESUME.md` file from the knowledge base:

```bash
python3 generate_resume.py
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
