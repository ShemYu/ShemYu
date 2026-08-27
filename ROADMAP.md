# Project Roadmap

This document outlines the future development plans for the Career History Knowledge Base.

## Phase 1: Automation & CI/CD
- [x] **GitHub Actions Workflow**: Automatically generate the profile and resume whenever source data changes on `main`.
- [ ] **Release Management**: Automatically tag versions and release PDF/Markdown artifacts.

## Phase 2: Enhanced Generation
- [ ] **Multiple Templates**: Support different resume styles (e.g., Classic, Modern, Tech-focused).
- [x] **HTML Support**: Generate HTML versions alongside Markdown.
- [ ] **PDF Support**: Generate a PDF from the HTML resume.

## Phase 3: Profile Integration
- [x] **GitHub Profile Sync**: Generate the GitHub profile `README.md` from the same career data.
- [ ] **Personal Website**: Generate a static website (e.g., using Hugo or Jekyll) from the YAML data.

## Phase 4: Data Quality
- [x] **Schema Validation**: Validate every YAML-backed profile with shared Pydantic models before rendering.
- [ ] **Linting**: Add linting for YAML files.

## Remaining usability work
1. **Guided wiki editing**: Adding or updating pages under `career/` is still manual.
2. **PDF releases**: HTML-to-PDF export and versioned release artifacts are not automated yet.
