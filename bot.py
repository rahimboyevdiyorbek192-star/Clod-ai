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

HELP_TEXT = (
    "👋 Ustoz.ai Avtomatik Ro'yxatdan O'tkazish Boti\n\n"
    "📊 Excel (.xlsx) faylni yuboring.\n"
    "Birinchi qator sarlavha bo'lishi kerak:\n\n"
    "  email | ism | familiya | parol | promo\n\n"
    "Email uchun Gmail alias ishlatish tavsiya etiladi:\n"
    "  sizningmail+1@gmail.com\n"
    "  sizningmail+2@gmail.com\n"
    "  s.izningmail@gmail.com\n\n"
    "Barchasi bitta inboxga keladi — OTP avtomatik o'qiladi!\n\n"
    "Gmail App Password sozlash:\n"
    "Gmail → Xavfsizlik → 2-bosqichli tasdiqlash →\n"
    "App Passwords → 16 ta belgili parol → .env ga yozing"
)

EXAMPLE_ROW = (
    "Namuna:\n"
    "email                          | ism  | familiya | parol    | promo\n"
    "rahimboyevdiyorbek192+1@gmail  | Ali  | Valiyev  | Pass123! |\n"
    "r.ahimboyevdiyorbek192@gmail   | Vali | Karimov  | Pass456! |\n"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document

    if not doc.file_name.lower().endswith((".xlsx", ".xls")):
        await update.message.reply_text("❌ Faqat .xlsx Excel fayl yuboring!")
        return

    status = await update.message.reply_text("📥 Excel o'qilmoqda...")

    try:
        tg_file = await doc.get_file()
        raw = await tg_file.download_as_bytearray()
        users = parse_excel(bytes(raw))
    except Exception as exc:
        await status.edit_text(f"❌ Excel o'qishda xato: {exc}")
        return

    if not users:
        await status.edit_text("❌ Foydalanuvchi topilmadi!\n\n" + EXAMPLE_ROW)
        return

    await status.edit_text(
        f"📋 {len(users)} ta foydalanuvchi topildi.\n"
        "⏳ Ro'yxatdan o'tkazish boshlandi (to'liq avtomatik)..."
    )

    ok_count = 0
    fail_count = 0
    results: list[dict] = []

    for i, user in enumerate(users, start=1):
        email = user["email"]

        async def update_status(msg: str, _i=i, _email=email):
            try:
                await status.edit_text(
                    f"⏳ {_i}/{len(users)}: {_email}\n"
                    f"✅ {ok_count} muvaffaqiyat  ❌ {fail_count} xato\n\n"
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
            status_cb=update_status,
        )

        results.append(result)
        if result["success"]:
            ok_count += 1
        else:
            fail_count += 1

        if i < len(users):
            await asyncio.sleep(3)  # Ro'yxatdan o'tishlar orasida pauza

    # ── Yakuniy hisobot ───────────────────────────────────────────────────────
    lines = [
        f"📊 Yakuniy hisobot ({len(users)} ta):",
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
        await status.edit_text(f"📊 Hisobot:\n✅ {ok_count}  ❌ {fail_count}")
        chunk: list[str] = []
        for line in lines[4:]:
            chunk.append(line)
            if len("\n".join(chunk)) > 3800:
                await update.message.reply_text("\n".join(chunk[:-1]))
                chunk = [line]
        if chunk:
            await update.message.reply_text("\n".join(chunk))


def main():
    if not BOT_TOKEN:
        raise SystemExit("❌ BOT_TOKEN topilmadi! .env ga BOT_TOKEN kiriting.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Bot ishga tushdi ✅")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
