import os

SYSTEM = """Siz kiberxavfsizlik bo'yicha mutaxassis yordamchisiz (Clod-AI Security).
Quyidagi sohalarda yordam bering:
- CTF (Capture the Flag) musobaqa masalalarini hal qilish
- Zaifliklar va CVE-larni tushuntirish
- Penetratsion testlash (faqat ruxsat berilgan muhitlarda)
- Tarmoq xavfsizligi, kriptografiya, veb xavfsizligi (OWASP Top 10)
- Himoya strategiyalari va xavfsizlik me'moriyati
- Log tahlili va tahdidlarni aniqlash
- Zararli dasturlarni statik tahlil qilish
- Forensika va hodisalarga javob berish

Buzg'unchilik, DoS hujumlari, noqonuniy maqsadlar uchun yordam bermang.
O'zbek, rus va ingliz tillarida javob bering."""

_anthropic_client = None


def _use_cloud() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import Anthropic
        _anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _anthropic_client


async def chat(messages: list[dict]) -> str:
    if _use_cloud():
        resp = _get_anthropic().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=SYSTEM,
            messages=messages,
        )
        return resp.content[0].text
    else:
        from modules import local_ai
        return await local_ai.chat(messages, system=SYSTEM)
