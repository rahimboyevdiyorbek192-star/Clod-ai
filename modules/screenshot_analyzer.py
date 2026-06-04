import base64
import os

SYSTEM = """Siz kiberxavfsizlik bo'yicha tajribali ekspertsiz.
Rasmni tahlil qilib, xavfsizlik nuqtai nazaridan batafsil baholang:
1. Aniqlangan muammolar — zaifliklar, noto'g'ri sozlamalar
2. Hujum belgilari — shubhali trafiklar, zararli kodlar
3. Texnologiyalar — OS, xizmatlar, versiyalar
4. Tavsiyalar — har bir topilma uchun tuzatish choralari
5. Xavf darajasi — Past / O'rta / Yuqori / Kritik
O'zbek tilida yozing."""


def _use_cloud() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


async def analyze(image_bytes: bytes, media_type: str = "image/png") -> str:
    if _use_cloud():
        from anthropic import Anthropic
        b64 = base64.standard_b64encode(image_bytes).decode()
        client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=SYSTEM,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                    {"type": "text", "text": "Bu skrinshotni kiberxavfsizlik nuqtai nazaridan tahlil qiling."},
                ],
            }],
        )
        return resp.content[0].text
    else:
        from modules import local_ai
        prompt = (
            f"{SYSTEM}\n\n"
            "Bu skrinshotni kiberxavfsizlik nuqtai nazaridan tahlil qiling."
        )
        return await local_ai.vision(image_bytes, prompt)
