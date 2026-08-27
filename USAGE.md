# Career wiki and resume views

`career/**/*.md` is the source of truth: a wiki people can read and a graph programs can query. YAML frontmatter is the node; the Markdown body is the wiki. Resume files are **views** under `views/`. Do not author career facts in templates or generated HTML.

Public views may add a document-specific headline, summary, or editorial rewrite beside a source claim id. A rewrite may compress or improve the wording, but it must not introduce a fact that is absent from the referenced public claim. When implementation and outcome are stored separately, add their ids under `supporting_claims`; the renderer validates every source and records the complete provenance for that one bullet. Every role, bullet, skill, education item, certificate, and award selected by a view is rendered exactly once; templates do not silently clip the selection.

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
- `output/pdf/shem-yu-resume.pdf`: English one-page PDF, rendered and page-count checked
- `output/resume_bible.html`: full + internal evidence (`views/bible.yaml`)

Japanese (also writes and checks `output/pdf/shem-yu-resume-ja.pdf`):

```bash
uv run --locked python -m src.main --language ja
```

Claim Japanese lives on the claim node (`text.ja`). Axis tags and document order live on the view. The job fails if either English or Japanese PDF is not exactly one page.

Single view:

```bash
uv run --locked python -m src.main --view one-pager
```

Detailed English master resume (natural multi-page layout, no one-page gate):

```bash
uv run --locked python -m src.main --view detailed
```

This writes `output/resume-detailed.html` and
`output/pdf/shem-yu-resume-detailed.pdf`. The detailed view preserves the
one-page version and is currently English-only.

For `senior-impact-v1`, write bullets as implementation and ownership first, followed by context and an evidence-backed outcome. Tool-first and metric-first openings fail validation. Multi-claim bullets require an explicit editorial rewrite in each rendered locale, and exact tests in `tests/test_graph.py` lock the approved English wording for both `one-pager` and `detailed`.

## Add a focus or claim

Create `career/foci/<id>.md` and `career/claims/<id>.md`. Filename must equal `id`. Link `focus.role`, `claim.focus`, and `stack` to existing ids. Public views may only list `disclosure: public` claims.

See [RESUME.md](./RESUME.md) for the latest generated Markdown resume.
