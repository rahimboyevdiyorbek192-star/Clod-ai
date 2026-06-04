"""
OSINT bot uchun AI xulosa moduli.
ANTHROPIC_API_KEY bo'lsa → Claude Haiku (bulut)
Bo'lmasa           → Ollama mahalliy model (offline, bepul)
"""
import os

SYSTEM = (
    "Siz kiberxavfsizlik va OSINT tahlilchisisiz. "
    "O'zbek tilida qisqa, aniq va professional xulosa yozing."
)

_anthropic_client = None


def _use_cloud() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import AsyncAnthropic
        _anthropic_client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _anthropic_client


async def _ask(prompt: str, max_tokens: int = 500) -> str:
    if _use_cloud():
        resp = await _get_anthropic().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    else:
        from modules import local_ai
        return await local_ai.chat(
            [{"role": "user", "content": prompt}],
            system=SYSTEM,
        )


async def summarize_scan(target: str, count: int, users_sample: list[dict]) -> str:
    bios        = [u.get("bio", "")            for u in users_sample if u.get("bio")][:15]
    private_ch  = sum(1 for u in users_sample if u.get("private_channels"))
    personal_ch = sum(1 for u in users_sample if u.get("personal_channel"))
    bots        = sum(1 for u in users_sample if u.get("is_bot"))
    premium     = sum(1 for u in users_sample if u.get("is_premium"))

    prompt = (
        f"Skanerlangan manba: {target}\n"
        f"Jami profil: {count} ta | Namuna: {len(users_sample)} ta\n"
        f"  • Shaxsiy kanal: {personal_ch} | Maxfiy kanal bio-da: {private_ch}\n"
        f"  • Botlar: {bots} | Premium: {premium}\n\n"
        "Bio namunalari:\n"
        + "\n".join(f"• {b[:120]}" for b in bios[:10])
        + "\n\n"
        "1. Asosiy topilmalar va naqshlar\n"
        "2. Diqqatga sazovor profillar\n"
        "3. Chuqurroq tekshirish tavsiyalari\n"
        "5-7 jumlada professional xulosa yozing."
    )
    return await _ask(prompt)


async def summarize_keywords(keyword: str, results: list[dict]) -> str:
    sources      = list({r.get("source", "") for r in results})
    texts        = [r.get("text", "") for r in results if r.get("text")]
    unique_users = len({r.get("user_id", "") for r in results})

    prompt = (
        f'Kalit so\'z: "{keyword}"\n'
        f"Topildi: {len(results)} | Noyob muallif: {unique_users}\n"
        f"Manbalar: {', '.join(str(s) for s in sources[:5])}\n\n"
        "Xabar namunalari:\n"
        + "\n".join(f"• {t[:150]}" for t in texts[:12])
        + "\n\n"
        "1. Mavzu va kontekst\n"
        "2. G'ayrioddiy topilmalar\n"
        "3. Xavfsizlik jihatdan diqqatga sazovorlar\n"
        "4-6 jumlada xulosa yozing."
    )
    return await _ask(prompt, max_tokens=400)


async def generate_status_report(stats: dict) -> str:
    prompt = (
        "OSINT platforma holati:\n"
        f"  • Foydalanuvchilar: {stats.get('total_users', 0):,}\n"
        f"  • Kesh xabarlari: {stats.get('total_messages', 0):,}\n"
        f"  • Manbalar: {stats.get('total_sources', 0)}\n"
        f"  • Knocker kanallar: {stats.get('knocker_count', 0)}\n"
        f"  • Musiqa barmoq izlari: {stats.get('music_fingerprints', 0):,}\n"
        f"  • Kuzatilayotgan musiqalar: {stats.get('watch_count', 0)}\n"
        f"  • Oxirgi skanerlash: {stats.get('last_scan', 'yo\'q')}\n\n"
        "1. Platforma faoliyati baholash\n"
        "2. Qaysi yo'nalishlarda yanada qidirish\n"
        "3. Keyingi tavsiya etiladigan qadamlar\n"
        "4-6 jumlada xulosa yozing."
    )
    return await _ask(prompt, max_tokens=400)
