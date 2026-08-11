"""List models visible to the configured OpenAI API account."""

import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional tailoring extra.
    load_dotenv = None


if load_dotenv is not None:
    load_dotenv(override=False)

if not os.environ.get("OPENAI_API_KEY", "").strip():
    print("OPENAI_API_KEY not found.")
else:
    from openai import OpenAI

    client = OpenAI()
    for model in client.models.list().data:
        print(model.id)
