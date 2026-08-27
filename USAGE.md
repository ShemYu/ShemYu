# Career wiki and resume views

`career/**/*.md` is the source of truth: a wiki people can read and a graph programs can query. YAML frontmatter is the node; the Markdown body is the wiki. Resume files are **views** under `views/`. Do not author career facts in templates or generated HTML.

`data/` is the previous YAML snapshot. This change does not delete it.

```text
career/          wiki + graph (SoT)
views/           which node ids appear on which document, in what order
src/graph/       parse and validate the vault
src/render/      bind a view to templates
templates/       print layout only
```

## Evidence-first content standard

Capture detail on the wiki page before compressing it into a claim `text`. Keep employment dates, focus windows, and experiment windows separate. Distinguish confirmed, derived, interview-needed, and do-not-claim statuses. Internal metrics stay `disclosure: internal` and can appear on the Bible view; they never belong on `views/one-pager.yaml`.

See [`RESUME_STANDARD.md`](RESUME_STANDARD.md) and [`career/INTERVIEW.md`](career/INTERVIEW.md). Long private narrative that must not be committed goes in `career/private/` (gitignored).

## Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)

```bash
uv sync --locked
```

## Update canonical artifacts

1. Edit or add pages under `career/`.
2. If the **one-pager / Markdown / Bible selection** should change, edit `views/*.yaml` — not the node.
3. Render:

```bash
uv run --locked python -m src.main
```

This writes:

- `README.md`: GitHub profile (`views/github-readme.yaml`)
- `RESUME.md`: full public Markdown (`views/full.yaml`)
- `output/resume.html`: A4 one-pager (`views/one-pager.yaml`)
- `output/resume_bible.html`: full + internal evidence (`views/bible.yaml`)

Japanese:

```bash
uv run --locked python -m src.main --language ja
```

Claim Japanese lives on the claim node (`text.ja`). Axis tags and clip order live on the view. The job fails if the Japanese PDF is not exactly one page.

Single view:

```bash
uv run --locked python -m src.main --view one-pager
```

## Add a focus or claim

Create `career/foci/<id>.md` and `career/claims/<id>.md`. Filename must equal `id`. Link `focus.role`, `claim.focus`, and `stack` to existing ids. Public views may only list `disclosure: public` claims.

See [RESUME.md](./RESUME.md) for the latest generated Markdown resume.
