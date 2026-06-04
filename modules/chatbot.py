import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

SYSTEM_PROMPT = """Siz Clod-AI platformasining aqlli yordamchisisiz.
Foydalanuvchilarga o'zbek, rus va ingliz tillarida yordam bering.
Qisqa, aniq va foydali javoblar bering."""


def chat(messages: list[dict]) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text
