# Career Evidence Workflow

Detailed interview notes and local artifacts. The committed source of truth
is the wiki+graph under [`career/`](../career/README.md). Resume selection
lives under [`views/`](../views/).

## Storage layers

| Layer | Location | Purpose |
|---|---|---|
| Wiki + graph | `career/**/*.md` | Nodes, links, locked claim text, metric contracts, `do_not_claim`. |
| Private vault | `career/private/` | Same schema; gitignored internal narrative. |
| Interview notes | `career_evidence/private/` | Legacy long masters; gitignored. Promote into `career/` claims, do not leave facts only here. |
| Tracked Git-history inventory | `career_evidence/moment_coach_ai_git_history.md` | Main-branch contribution ledger and resume-use boundaries derived from Moment Coach AI commits. |
| Legacy YAML snapshot | `data/` | Previous JSON-Resume tree. Kept; generator no longer treats it as live SoT. |
| Views | `views/*.yaml` | Which public claim ids appear on which resume, and in what order. |
| Canonical outputs | `README.md`, `RESUME.md`, `output/resume*.html` | Generated. Never edit to introduce a career fact. |

The current Cookpad master is `career_evidence/private/cookpad.md`. Its Obsidian copy is a research mirror; the repo-local file is the working private narrative.

## Evidence states

Use `status` on claim frontmatter:

- `confirmed`: reproduced or owner-confirmed
- `derived`: arithmetic from verified inputs
- `interview-needed`: materially affects scope and cannot be inferred
- `do-not-claim`: unsupported, confidential, or misleading

See [`career/INTERVIEW.md`](../career/INTERVIEW.md) for open questions.

## Workflow

1. Capture the fact on a `career/` page (or `career/private/` if it must not be committed).
2. Set `disclosure`, `status`, metric contract, and `do_not_claim`.
3. To change a resume, add or reorder the claim id in `views/*.yaml`.
4. Render with `uv run --locked python -m src.main`.
