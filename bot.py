import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from excel_parser import parse_excel
from register import register_user

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

HELP_TEXT = """
👋 *Ustoz.ai Ro'yxatdan O'tkazish Boti*

📊 Foydalanish:
Excel (.xlsx) faylni yuboring. Birinchi qator sarlavha bo'lishi kerak:

| email | ism | familiya | parol | imap\_parol | promo |
|-------|-----|----------|-------|-------------|-------|
| user@gmail.com | Ali | Valiyev | Pass123! | gmailappparol | (ixtiyoriy) |

🔑 *imap\_parol* — bu Gmail App Password (oddiy parol emas\!):
Gmail → Sozlamalar → Xavfsizlik → 2-bosqichli tasdiqlash → App Passwords → 16 belgili parol

⚡ Bot har bir emailni ustoz\.ai da ro'yxatdan o'tkazadi va OTP ni avtomatik o'qiydi\.
"""

EXAMPLE_ROW = (
    "Namuna:\n"
    "email            | ism   | familiya | parol    | imap_parol       | promo\n"
    "user@gmail.com   | Ali   | Valiyev  | Pass123! | abcd efgh ijkl mn| (bo'sh)\n"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown_v2(HELP_TEXT)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown_v2(HELP_TEXT)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document

    if not doc.file_name.lower().endswith((".xlsx", ".xls")):
        await update.message.reply_text("❌ Faqat .xlsx Excel fayl yuboring!")
        return

    status = await update.message.reply_text("📥 Excel fayl o'qilmoqda...")

    try:
        tg_file = await doc.get_file()
        raw = await tg_file.download_as_bytearray()
        users = parse_excel(bytes(raw))
    except Exception as exc:
        await status.edit_text(f"❌ Excel o'qishda xato: {exc}")
        return

    if not users:
        await status.edit_text(
            "❌ Foydalanuvchi topilmadi!\n\n"
            "Ustunlarni tekshiring:\n"
            + EXAMPLE_ROW
        )
        return

    missing_imap = [u["email"] for u in users if not u.get("imap_parol")]
    if missing_imap:
        warn = (
            f"⚠️ {len(missing_imap)} ta foydalanuvchida imap_parol yo'q:\n"
            + "\n".join(f"  • {e}" for e in missing_imap[:10])
            + ("\n  ..." if len(missing_imap) > 10 else "")
            + "\n\nBu emaillar OTP bosqichida to'xtaydi."
        )
        await update.message.reply_text(warn)

    await status.edit_text(
        f"📋 {len(users)} ta foydalanuvchi topildi.\n"
        "⏳ Ro'yxatdan o'tkazish boshlandi. Kuting..."
    )

    results: list[dict] = []
    ok_count = 0
    fail_count = 0

    for i, user in enumerate(users, start=1):
        email = user["email"]
        short_status = (
            f"⏳ {i}/{len(users)}: {email}\n"
            f"✅ {ok_count} muvaffaqiyat  ❌ {fail_count} xato"
        )

        try:
            await status.edit_text(short_status)
        except Exception:
            pass

        async def _cb(msg: str, _email=email, _idx=i, _ok=ok_count, _fail=fail_count):
            try:
                await status.edit_text(
                    f"⏳ {_idx}/{len(users)}: {_email}\n"
                    f"✅ {_ok} muvaffaqiyat  ❌ {_fail} xato\n\n"
                    f"▶ {msg}"
                )
            except Exception:
                pass

        result = await register_user(
            email=email,
            ism=user.get("ism", ""),
            familiya=user.get("familiya", ""),
            parol=user.get("parol", ""),
            promo=user.get("promo", ""),
            imap_password=user.get("imap_parol", ""),
            status_cb=_cb,
        )

        results.append(result)
        if result["success"]:
            ok_count += 1
        else:
            fail_count += 1

        if i < len(users):
            await asyncio.sleep(2)

    # ── Final report ──────────────────────────────────────────────────────────
    lines = [
        f"📊 *Yakuniy hisobot* ({len(users)} ta foydalanuvchi)",
        f"✅ Muvaffaqiyat: {ok_count}",
        f"❌ Xato: {fail_count}",
        "",
    ]
    for r in results:
        lines.append(r["message"])

    report = "\n".join(lines)

    if len(report) <= 4000:
        await status.edit_text(report)
    else:
        await status.edit_text(
            f"📊 *Yakuniy hisobot*\n✅ {ok_count} muvaffaqiyat  ❌ {fail_count} xato"
        )
        # Send detailed log in chunks
        chunk_lines: list[str] = []
        for line in lines[4:]:
            chunk_lines.append(line)
            if len("\n".join(chunk_lines)) > 3800:
                await update.message.reply_text("\n".join(chunk_lines[:-1]))
                chunk_lines = [line]
        if chunk_lines:
            await update.message.reply_text("\n".join(chunk_lines))


def main():
    if not BOT_TOKEN:
        raise SystemExit("❌ BOT_TOKEN topilmadi! .env faylida BOT_TOKEN ni kiriting.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Bot ishga tushdi ✅")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
