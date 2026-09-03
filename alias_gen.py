"""
Gmail alias generator.

Gmail da barcha quyidagi variantlar bir inboxga keladi:
  user+1@gmail.com, user+2@gmail.com, ...  (+ trick)
  u.ser@gmail.com, us.er@gmail.com, ...    (dot trick)

Bu modul + trick ishlatadi: oddiy, ishonchli va cheksiz.
Alias counter gmail_creds.json da saqlanadi — har safar davom etadi.
"""

import json
from pathlib import Path

CREDS_FILE = Path("gmail_creds.json")


def _load() -> dict:
    if CREDS_FILE.exists():
        try:
            return json.loads(CREDS_FILE.read_text())
        except Exception:
            pass
    return {}


def _save(data: dict):
    CREDS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def get_current_counter() -> int:
    return _load().get("alias_counter", 0)


def next_alias(base_email: str, count: int = 1) -> list[str]:
    """
    base_email uchun keyingi `count` ta alias qaytaradi va counter ni saqlaydi.

    Masalan:
        base_email = "rahimboyevdiyorbek192@gmail.com"
        next_alias(base_email, 3)
        → ["rahimboyevdiyorbek192+1@gmail.com",
           "rahimboyevdiyorbek192+2@gmail.com",
           "rahimboyevdiyorbek192+3@gmail.com"]
    """
    data = _load()
    start = data.get("alias_counter", 0) + 1
    username, domain = base_email.split("@")

    aliases = [f"{username}+{i}@{domain}" for i in range(start, start + count)]

    data["alias_counter"] = start + count - 1
    _save(data)

    return aliases


def reset_counter():
    """Alias counter ni nolga qaytarish."""
    data = _load()
    data["alias_counter"] = 0
    _save(data)
