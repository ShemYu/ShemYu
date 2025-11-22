# Project Roadmap

This document outlines the future development plans for the Career History Knowledge Base.

## Phase 1: Automation & CI/CD
- [ ] **GitHub Actions Workflow**: Automatically generate `RESUME.md` whenever a change is pushed to the `data/` directory.
- [ ] **Release Management**: Automatically tag versions and release PDF/Markdown artifacts.

## Phase 2: Enhanced Generation
- [ ] **Multiple Templates**: Support different resume styles (e.g., Classic, Modern, Tech-focused).
- [ ] **Format Support**: Generate PDF (via LaTeX or HTML-to-PDF) and HTML versions alongside Markdown.
- [ ] **Cover Letter Generator**: Generate basic cover letters based on the profile and a job description.

## Phase 3: Profile Integration
- [ ] **GitHub Profile Sync**: Re-implement the feature to inject a summary or selected section into the main `README.md` (optional/configurable).
- [ ] **Personal Website**: Generate a static website (e.g., using Hugo or Jekyll) from the YAML data.

## Phase 4: Data Quality
- [ ] **Schema Validation**: Implement JSON Schema or Pydantic models to validate YAML files to ensure data integrity.
- [ ] **Linting**: Add linting for YAML files.
