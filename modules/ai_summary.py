import os
from anthropic import AsyncAnthropic

_client = None

SYSTEM = (
    "Siz kiberxavfsizlik va OSINT (ochiq manba razvedka) tahlilchisisiz. "
    "O'zbek tilida qisqa, aniq va professional xulosa yozing."
)


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    return _client


async def summarize_scan(target: str, count: int, users_sample: list[dict]) -> str:
    """Guruh/kanal skanerlash natijalarini Claude bilan tahlil qiladi."""
    bios = [u.get("bio", "") for u in users_sample if u.get("bio")][:15]
    private_ch = sum(1 for u in users_sample if u.get("private_channels"))
    personal_ch = sum(1 for u in users_sample if u.get("personal_channel"))
    bots = sum(1 for u in users_sample if u.get("is_bot"))
    premium = sum(1 for u in users_sample if u.get("is_premium"))

    prompt = (
        f"Skanerlangan manba: {target}\n"
        f"Jami profil: {count} ta\n"
        f"Namuna: {len(users_sample)} ta ko'rildi\n"
        f"  • Shaxsiy kanal: {personal_ch} ta\n"
        f"  • Maxfiy kanal havolasi bio-da: {private_ch} ta\n"
        f"  • Botlar: {bots} ta | Premium: {premium} ta\n\n"
        f"Bio namunalari:\n"
        + "\n".join(f"• {b[:120]}" for b in bios[:10])
        + "\n\nUshbu OSINT skanerlash natijalari asosida:\n"
        "1. Asosiy topilmalar va naqshlar\n"
        "2. Diqqatga sazovor profillar yoki havolalar\n"
        "3. Qaysi profillar/kanallarni chuqurroq tekshirish kerak\n"
        "5-8 jumlada professional xulosa yozing."
    )
    resp = await _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


async def summarize_keywords(keyword: str, results: list[dict]) -> str:
    """Kalit so'z qidiruv natijalarini tahlil qiladi."""
    sources = list({r.get("source", "") for r in results})
    texts = [r.get("text", "") for r in results if r.get("text")]
    unique_users = len({r.get("user_id", "") for r in results})

    prompt = (
        f'Kalit so\'z: "{keyword}"\n'
        f"Topilgan natijalar: {len(results)} ta\n"
        f"Noyob mualliflar: {unique_users} kishi\n"
        f"Manbalar: {', '.join(str(s) for s in sources[:6])}\n\n"
        f"Xabar namunalari:\n"
        + "\n".join(f"• {t[:150]}" for t in texts[:12])
        + "\n\nUshbu qidiruv natijalari asosida:\n"
        "1. Mavzu va kontekst tahlili\n"
        "2. Muhim naqshlar yoki g'ayrioddiy topilmalar\n"
        "3. Xavfsizlik jihatidan diqqatga sazovorlar\n"
        "4-6 jumlada professional xulosa yozing."
    )
    resp = await _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


async def generate_status_report(stats: dict) -> str:
    """Umumiy platforma holati bo'yicha AI hisobot."""
    prompt = (
        "OSINT platformasi joriy holati:\n"
        f"  • Skanerlangan foydalanuvchilar: {stats.get('total_users', 0):,}\n"
        f"  • Lokal kesh xabarlari: {stats.get('total_messages', 0):,}\n"
        f"  • Monitoring manbalari: {stats.get('total_sources', 0)}\n"
        f"  • Maxfiy kanal (knocker): {stats.get('knocker_count', 0)} ta\n"
        f"  • Musiqa barmoq izlari: {stats.get('music_fingerprints', 0):,}\n"
        f"  • Kuzatilayotgan musiqalar: {stats.get('watch_count', 0)} ta\n"
        f"  • Oxirgi skanerlash: {stats.get('last_scan', 'nomalum')}\n\n"
        "Ushbu holat ma'lumotlari asosida:\n"
        "1. Platforma faoliyatini baholash\n"
        "2. Qaysi yo'nalishlarda yanada qidirish tavsiya etiladi\n"
        "3. Keyingi tavsiya etiladigan qadamlar\n"
        "4-6 jumlada professional xulosa yozing."
    )
    resp = await _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text
