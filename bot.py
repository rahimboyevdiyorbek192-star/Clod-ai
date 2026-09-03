import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from excel_parser import parse_excel
from register import register_user

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CREDS_FILE = Path("gmail_creds.json")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ConversationHandler holatlari
ASK_EMAIL, ASK_PASSWORD = range(2)


# ─── Credentials (saqlash/yuklash) ───────────────────────────────────────────

def load_creds() -> dict:
    """Saqlangan Gmail ma'lumotlarini yuklash."""
    if CREDS_FILE.exists():
        try:
            return json.loads(CREDS_FILE.read_text())
        except Exception:
            pass
    return {}


def save_creds(email: str, password: str, server: str = "imap.gmail.com"):
    """Gmail ma'lumotlarini faylga saqlash."""
    CREDS_FILE.write_text(
        json.dumps({"email": email, "password": password, "server": server}, ensure_ascii=False)
    )


def get_creds() -> tuple[str, str, str] | None:
    """(email, password, server) yoki None qaytaradi."""
    c = load_creds()
    if c.get("email") and c.get("password"):
        return c["email"], c["password"], c.get("server", "imap.gmail.com")
    return None


# ─── Klaviatura ──────────────────────────────────────────────────────────────

def main_keyboard(creds_connected: bool) -> InlineKeyboardMarkup:
    if creds_connected:
        email = load_creds().get("email", "")
        btn_label = f"✅ Gmail: {email}"
        btn_action = "change_gmail"
    else:
        btn_label = "📧 Gmail ulash"
        btn_action = "connect_gmail"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(btn_label, callback_data=btn_action)],
        [InlineKeyboardButton("❓ Yordam", callback_data="help")],
    ])


# ─── Handlers ────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    creds = get_creds()
    text = (
        "👋 *Ustoz.ai Ro'yxatdan O'tkazish Boti*\n\n"
        + (
            f"✅ Gmail ulangan: `{creds[0]}`\n\n"
            "Excel faylni yuboring — bot o'zi ro'yxatdan o'tkazadi!"
            if creds else
            "⚠️ Gmail ulanmagan.\n\n"
            "Avval Gmail ni ulang, keyin Excel yuboring."
        )
    )
    await update.message.reply_markdown(
        text,
        reply_markup=main_keyboard(creds is not None),
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Foydalanish:\n\n"
        "1. /start → 'Gmail ulash' tugmasini bosing\n"
        "2. Email va App Password kiriting\n"
        "3. Excel fayl yuboring\n\n"
        "Excel ustunlari:\n"
        "  email | ism | familiya | parol | promo\n\n"
        "Gmail alias misoli:\n"
        "  sizningmail+1@gmail.com\n"
        "  sizningmail+2@gmail.com\n"
        "  s.izningmail@gmail.com\n\n"
        "App Password olish:\n"
        "Gmail → Xavfsizlik → 2FA → App Passwords"
    )


# ── Gmail ulash (ConversationHandler) ────────────────────────────────────────

async def btn_connect_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'Gmail ulash' tugmasi bosilganda."""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "📧 Gmail manzilingizni yuboring:\n\n"
        "Masalan: `sizningmail@gmail.com`",
        parse_mode="Markdown",
    )
    return ASK_EMAIL


async def btn_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "📖 Foydalanish:\n\n"
        "1. Gmail ulash tugmasini bosing\n"
        "2. Excel (.xlsx) yuboring\n\n"
        "Gmail App Password olish:\n"
        "Gmail → Xavfsizlik → 2FA → App Passwords → 16 ta belgi"
    )
    return ConversationHandler.END


async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi email yozdi."""
    email = update.message.text.strip()
    if "@" not in email or "." not in email:
        await update.message.reply_text("❌ Noto'g'ri email format. Qayta yuboring:")
        return ASK_EMAIL

    context.user_data["gmail_email"] = email
    await update.message.reply_text(
        f"✅ Email: `{email}`\n\n"
        "🔑 Endi Gmail *App Password* ni yuboring (16 ta belgi):\n\n"
        "Olish yo'li:\n"
        "Gmail → Xavfsizlik → 2-bosqichli tasdiqlash → App Passwords\n\n"
        "_Masalan: abcd efgh ijkl mnop_",
        parse_mode="Markdown",
    )
    return ASK_PASSWORD


async def ask_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi App Password yozdi."""
    password = update.message.text.strip().replace(" ", "")

    if len(password) < 12:
        await update.message.reply_text(
            "❌ App Password 16 ta belgi bo'lishi kerak.\n"
            "Gmail → Xavfsizlik → App Passwords dan oling.\n\n"
            "Qayta yuboring:"
        )
        return ASK_PASSWORD

    email = context.user_data.get("gmail_email", "")
    raw_password = update.message.text.strip()  # bo'shliqlar bilan saqlash

    # Xabarni o'chirish (maxfiylik uchun)
    try:
        await update.message.delete()
    except Exception:
        pass

    # IMAP server aniqlash
    domain = email.split("@")[-1].lower()
    imap_servers = {
        "gmail.com": "imap.gmail.com",
        "mail.ru": "imap.mail.ru",
        "yandex.ru": "imap.yandex.ru",
        "outlook.com": "outlook.office365.com",
        "hotmail.com": "outlook.office365.com",
    }
    server = imap_servers.get(domain, f"imap.{domain}")

    save_creds(email, raw_password, server)

    await update.effective_chat.send_message(
        f"✅ *Gmail ulandi!*\n\n"
        f"📧 Email: `{email}`\n"
        f"🔒 Parol: ••••••••••••\n\n"
        "Endi Excel faylni yuboring!",
        parse_mode="Markdown",
        reply_markup=main_keyboard(True),
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END


# ── Excel handler ─────────────────────────────────────────────────────────────

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document

    if not doc.file_name.lower().endswith((".xlsx", ".xls")):
        await update.message.reply_text("❌ Faqat .xlsx Excel fayl yuboring!")
        return

    creds = get_creds()
    if not creds:
        await update.message.reply_text(
            "⚠️ Gmail ulanmagan!\n\n"
            "/start buyrug'ini bosib, avval Gmail ni ulang.",
            reply_markup=main_keyboard(False),
        )
        return

    imap_email, imap_password, imap_server = creds

    status = await update.message.reply_text("📥 Excel o'qilmoqda...")

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
            "Ustunlarni tekshiring: email | ism | familiya | parol | promo"
        )
        return

    await status.edit_text(
        f"📋 {len(users)} ta foydalanuvchi topildi.\n"
        f"📧 Gmail: {imap_email}\n"
        "⏳ Ro'yxatdan o'tkazish boshlandi (to'liq avtomatik)..."
    )

    ok_count = 0
    fail_count = 0
    results: list[dict] = []

    for i, user in enumerate(users, start=1):
        email = user["email"]

        async def update_status(msg: str, _i=i, _email=email, _ok=ok_count, _fail=fail_count):
            try:
                await status.edit_text(
                    f"⏳ {_i}/{len(users)}: {_email}\n"
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
            imap_email=imap_email,
            imap_password=imap_password,
            imap_server=imap_server,
            status_cb=update_status,
        )

        results.append(result)
        if result["success"]:
            ok_count += 1
        else:
            fail_count += 1

        if i < len(users):
            await asyncio.sleep(3)

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


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not BOT_TOKEN:
        raise SystemExit("❌ BOT_TOKEN topilmadi! .env ga BOT_TOKEN kiriting.")

    app = Application.builder().token(BOT_TOKEN).build()

    # Gmail ulash suhbati
    gmail_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(btn_connect_gmail, pattern="^(connect_gmail|change_gmail)$"),
        ],
        states={
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
            ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(gmail_conv)
    app.add_handler(CallbackQueryHandler(btn_help, pattern="^help$"))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Bot ishga tushdi ✅")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
