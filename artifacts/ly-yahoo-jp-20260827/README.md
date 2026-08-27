# LINE Yahoo Japanese 職務経歴書 (2026-08-27)

Live compose path (requires `OPENAI_API_KEY`):

```bash
uv run --locked --extra tailoring python -m src.main \
  artifacts/ly-yahoo-jp-20260827/jds/ly_platform_jp.txt \
  --language ja --output-name ly_platform_jp

uv run --locked --extra tailoring python -m src.main \
  artifacts/ly-yahoo-jp-20260827/jds/ly_agent_jp.txt \
  --language ja --output-name ly_agent_jp
```

Copy `output/tailored/ly_{platform,agent}_jp.{pdf,html,md}` into this folder after a successful run.

Do not email Beth. Do not apply. Do not merge these resume files into main.
