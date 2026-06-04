import base64
import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

SYSTEM_PROMPT = """Siz kiberxavfsizlik bo'yicha tajribali ekspertsiz.
Foydalanuvchi yuborgan rasm yoki skrinshotni tahlil qilib, xavfsizlik nuqtai nazaridan batafsil baholang.

Tahlil quyidagilarni o'z ichiga olsin (mavjud bo'lganlarini):
1. **Aniqlangan muammolar** — zaifliklar, noto'g'ri sozlamalar, xavfli konfiguratsiyalar
2. **Hujum belgilari** — shubhali trafiklar, zararli kodlar, anomaliyalar
3. **Texnologiyalar** — aniqlangan OS, xizmatlar, versiyalar va ularning xavfsizligi
4. **Tavsiyalar** — har bir topilma uchun aniq tuzatish choralari
5. **Xavf darajasi** — Past / O'rta / Yuqori / Kritik

Javobingiz aniq, qisqa va amaliy bo'lsin. O'zbek tilida yozing."""


def analyze(image_bytes: bytes, media_type: str = "image/png") -> str:
    b64 = base64.standard_b64encode(image_bytes).decode()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": b64},
                },
                {
                    "type": "text",
                    "text": "Bu skrinshotni kiberxavfsizlik nuqtai nazaridan tahlil qiling.",
                },
            ],
        }],
    )
    return response.content[0].text
