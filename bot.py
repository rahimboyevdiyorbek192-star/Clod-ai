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
from register import register_user_with_manual_otp

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

HELP_TEXT = (
    "👋 Ustoz.ai Ro'yxatdan O'tkazish Boti\n\n"
    "📊 Excel (.xlsx) faylni yuboring.\n"
    "Birinchi qator sarlavha bo'lishi kerak:\n\n"
    "  email | ism | familiya | parol | promo\n\n"
    "• promo — ixtiyoriy (do'st promokodi)\n\n"
    "Jarayon:\n"
    "1. Bot ro'yxatdan o'tishni boshlaydi\n"
    "2. OTP kelganda bot sizdan so'raydi\n"
    "3. Siz emailni ochib, 4 raqamli kodni yozasiz\n"
    "4. Bot kiritadi va davom etadi ✅"
)

EXAMPLE_ROW = (
    "Namuna:\n"
    "email            | ism  | familiya | parol    | promo\n"
    "ali@gmail.com    | Ali  | Valiyev  | Pass123! | (bo'sh)\n"
)

# chat_id → asyncio.Future[str]  (OTP kutilmoqda)
_otp_futures: dict[int, asyncio.Future] = {}


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """OTP yoki oddiy xabarlarni qabul qilish."""
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    fut = _otp_futures.get(chat_id)
    if fut and not fut.done():
        # Foydalanuvchi OTP yozdi
        digits = "".join(filter(str.isdigit, text))
        if len(digits) == 4:
            fut.set_result(digits)
            await update.message.reply_text(f"✅ OTP {digits} qabul qilindi, davom etilmoqda...")
        else:
            await update.message.reply_text("⚠️ 4 raqamli kod yuboring (masalan: 3847)")
    else:
        await update.message.reply_text("Excel fayl yuboring yoki /help yozing.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    chat_id = update.effective_chat.id

    if not doc.file_name.lower().endswith((".xlsx", ".xls")):
        await update.message.reply_text("❌ Faqat .xlsx Excel fayl yuboring!")
        return

    # Agar hozir boshqa jarayon ketayotgan bo'lsa
    existing = _otp_futures.get(chat_id)
    if existing and not existing.done():
        await update.message.reply_text("⚠️ Hozir boshqa ro'yxatdan o'tish jarayoni ketmoqda. Kuting.")
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
        "⏳ Ro'yxatdan o'tkazish boshlandi...\n\n"
        "OTP kelganda bu chatda so'rayman — emailni tayyor tuting! 📧"
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

        async def ask_otp(email_addr: str) -> str | None:
            """OTP ni foydalanuvchidan Telegram orqali so'rash."""
            loop = asyncio.get_event_loop()
            fut: asyncio.Future[str] = loop.create_future()
            _otp_futures[chat_id] = fut

            await update.effective_chat.send_message(
                f"📧 *{email_addr}* emailiga OTP kodi yuborildi.\n\n"
                f"Emailni oching va 4 raqamli kodni bu yerga yozing:\n"
                f"_(120 soniya vaqt bor)_",
                parse_mode="Markdown",
            )

            try:
                otp = await asyncio.wait_for(fut, timeout=120)
                return otp
            except asyncio.TimeoutError:
                await update.effective_chat.send_message(
                    f"⏰ {email_addr}: 120 soniya o'tdi, OTP kiritilmadi. O'tkazib yuborildi."
                )
                return None
            finally:
                _otp_futures.pop(chat_id, None)

        result = await register_user_with_manual_otp(
            email=email,
            ism=user.get("ism", ""),
            familiya=user.get("familiya", ""),
            parol=user.get("parol", ""),
            promo=user.get("promo", ""),
            otp_callback=ask_otp,
            status_cb=update_status,
        )

        results.append(result)
        if result["success"]:
            ok_count += 1
        else:
            fail_count += 1

        if i < len(users):
            await asyncio.sleep(2)

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
        chunks: list[str] = []
        chunk: list[str] = []
        for line in lines[4:]:
            chunk.append(line)
            if len("\n".join(chunk)) > 3800:
                chunks.append("\n".join(chunk[:-1]))
                chunk = [line]
        if chunk:
            chunks.append("\n".join(chunk))
        for c in chunks:
            await update.message.reply_text(c)


def main():
    if not BOT_TOKEN:
        raise SystemExit("❌ BOT_TOKEN topilmadi! .env faylida BOT_TOKEN ni kiriting.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot ishga tushdi ✅")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
