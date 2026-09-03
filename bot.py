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

from alias_gen import get_current_counter, next_alias, reset_counter
from excel_parser import parse_excel, has_email_column
from register import register_user

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CREDS_FILE = Path("gmail_creds.json")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

ASK_EMAIL, ASK_PASSWORD = range(2)


# ─── Credentials ─────────────────────────────────────────────────────────────

def load_creds() -> dict:
    if CREDS_FILE.exists():
        try:
            return json.loads(CREDS_FILE.read_text())
        except Exception:
            pass
    return {}


def save_creds(email: str, password: str, server: str = "imap.gmail.com"):
    data = load_creds()
    # Parolni bo'shliqsiz saqlash (Gmail App Password uchun ikki variant ham ishlaydi)
    data.update({"email": email, "password": password.replace(" ", ""), "server": server})
    CREDS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def get_creds() -> tuple[str, str, str] | None:
    c = load_creds()
    if c.get("email") and c.get("password"):
        return c["email"], c["password"], c.get("server", "imap.gmail.com")
    return None


# ─── Klaviatura ──────────────────────────────────────────────────────────────

def main_keyboard(connected: bool) -> InlineKeyboardMarkup:
    creds = load_creds()
    if connected and creds.get("email"):
        counter = creds.get("alias_counter", 0)
        gmail_btn = InlineKeyboardButton(
            f"✅ {creds['email']} (#{counter} alias)",
            callback_data="change_gmail",
        )
    else:
        gmail_btn = InlineKeyboardButton("📧 Gmail ulash", callback_data="connect_gmail")

    return InlineKeyboardMarkup([
        [gmail_btn],
        [InlineKeyboardButton("🔄 Alias counter reset", callback_data="reset_counter")],
        [InlineKeyboardButton("❓ Yordam", callback_data="help")],
    ])


# ─── /start ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    creds = get_creds()
    if creds:
        email, _, _ = creds
        counter = load_creds().get("alias_counter", 0)
        text = (
            f"👋 *Ustoz.ai Ro'yxatdan O'tkazish Boti*\n\n"
            f"✅ Gmail ulangan: `{email}`\n"
            f"📊 Hozirgacha {counter} ta alias ishlatildi\n\n"
            "Excel faylni yuboring:\n"
            "• Kerakli ustunlar: *ism | familiya | parol*\n"
            "• Email ustuni *kerak emas* — bot o'zi yaratadi\n"
            "• Ixtiyoriy: *promo*"
        )
    else:
        text = (
            "👋 *Ustoz.ai Ro'yxatdan O'tkazish Boti*\n\n"
            "⚠️ Gmail ulanmagan.\n\n"
            "Avval Gmail ni ulang, keyin Excel yuboring."
        )
    await update.message.reply_markdown(
        text,
        reply_markup=main_keyboard(creds is not None),
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Foydalanish:\n\n"
        "1. /start → 'Gmail ulash' tugmasini bosing\n"
        "2. Gmail va App Password kiriting\n"
        "3. Excel (.xlsx) yuboring\n\n"
        "Excel formati (email ustuni shart emas):\n"
        "  ism | familiya | parol | promo\n\n"
        "Bot o'zi emaillarni yaratadi:\n"
        "  sizningmail+1@gmail.com\n"
        "  sizningmail+2@gmail.com\n"
        "  ...\n\n"
        "App Password olish:\n"
        "Gmail → Xavfsizlik → 2FA → App Passwords"
    )


# ─── Gmail ulash (ConversationHandler) ───────────────────────────────────────

async def btn_connect_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "📧 Gmail manzilingizni yuboring:\n\n"
        "Masalan: `sizningmail@gmail.com`",
        parse_mode="Markdown",
    )
    return ASK_EMAIL


async def btn_reset_counter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    reset_counter()
    await query.message.reply_text(
        "🔄 Alias counter nolga qaytarildi.\n"
        "Keyingi ro'yxatdan o'tish +1 dan boshlanadi."
    )
    return ConversationHandler.END


async def btn_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "📖 Excel da faqat: ism | familiya | parol\n"
        "Email ustuni shart emas — bot o'zi yaratadi!\n\n"
        "App Password olish:\n"
        "Gmail → Xavfsizlik → 2FA → App Passwords"
    )
    return ConversationHandler.END


async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if "@" not in email or "." not in email:
        await update.message.reply_text("❌ Noto'g'ri email format. Qayta yuboring:")
        return ASK_EMAIL
    context.user_data["gmail_email"] = email
    await update.message.reply_text(
        f"✅ Email: `{email}`\n\n"
        "🔑 Gmail *App Password* ni yuboring (16 ta belgi):\n\n"
        "Olish yo'li:\n"
        "Gmail → Xavfsizlik → 2-bosqichli tasdiqlash → App Passwords\n\n"
        "_Masalan: abcd efgh ijkl mnop_",
        parse_mode="Markdown",
    )
    return ASK_PASSWORD


async def ask_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_password = update.message.text.strip()
    password_clean = raw_password.replace(" ", "")

    # Xabarni o'chirish (maxfiylik)
    try:
        await update.message.delete()
    except Exception:
        pass

    if len(password_clean) < 12:
        await update.effective_chat.send_message(
            "❌ App Password kamida 12 ta belgi bo'lishi kerak.\n"
            "Gmail → App Passwords dan oling. Qayta yuboring:"
        )
        return ASK_PASSWORD

    email = context.user_data.get("gmail_email", "")
    domain = email.split("@")[-1].lower()
    imap_servers = {
        "gmail.com":    "imap.gmail.com",
        "mail.ru":      "imap.mail.ru",
        "yandex.ru":    "imap.yandex.ru",
        "yandex.com":   "imap.yandex.ru",
        "outlook.com":  "outlook.office365.com",
        "hotmail.com":  "outlook.office365.com",
    }
    server = imap_servers.get(domain, f"imap.{domain}")

    # Bo'shliqsiz parolni saqlash
    save_creds(email, password_clean, server)
    counter = load_creds().get("alias_counter", 0)

    await update.effective_chat.send_message(
        f"✅ *Gmail ulandi!*\n\n"
        f"📧 `{email}`\n"
        f"📊 Hozirgacha {counter} ta alias ishlatilgan\n\n"
        "Endi Excel faylni yuboring!\n"
        "_(email ustuni kerak emas — bot o'zi yaratadi)_",
        parse_mode="Markdown",
        reply_markup=main_keyboard(True),
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END


# ─── Excel handler ────────────────────────────────────────────────────────────

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document

    # Faqat .xlsx qabul qilish
    if not doc.file_name.lower().endswith(".xlsx"):
        await update.message.reply_text(
            "❌ Faqat *Excel (.xlsx)* fayl yuboring!\n\n"
            "_.xls eski format — Excelda 'Excel Workbook (.xlsx)' deb saqlang._",
            parse_mode="Markdown",
        )
        return

    creds = get_creds()
    if not creds:
        await update.message.reply_text(
            "⚠️ Gmail ulanmagan! /start → 'Gmail ulash' tugmasini bosing.",
            reply_markup=main_keyboard(False),
        )
        return

    imap_email, imap_password, imap_server = creds
    status = await update.message.reply_text("📥 Excel o'qilmoqda...")

    try:
        tg_file = await doc.get_file()
        raw = await tg_file.download_as_bytearray()
        users, parse_errors = parse_excel(bytes(raw))
    except Exception as exc:
        await status.edit_text(f"❌ Excel o'qishda xato: {exc}")
        return

    if parse_errors:
        err_msg = "⚠️ Excel da xatolar:\n" + "\n".join(f"• {e}" for e in parse_errors[:10])
        if len(parse_errors) > 10:
            err_msg += f"\n...va yana {len(parse_errors)-10} ta"
        await update.message.reply_text(err_msg)

    if not users:
        await status.edit_text(
            "❌ To'g'ri foydalanuvchi topilmadi!\n\n"
            "Kerakli ustunlar: ism | familiya | parol\n"
            "(email ixtiyoriy)"
        )
        return

    # Email yo'q bo'lsa, alias generate qilish
    need_alias = not has_email_column(users)
    if need_alias:
        aliases = next_alias(imap_email, len(users))
        for user, alias in zip(users, aliases):
            user["email"] = alias

    counter_now = load_creds().get("alias_counter", 0)
    await status.edit_text(
        f"📋 {len(users)} ta foydalanuvchi topildi\n"
        + (f"📧 Alias: +{counter_now - len(users) + 1} → +{counter_now}\n" if need_alias else "")
        + "⏳ Ro'yxatdan o'tkazish boshlandi..."
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
                    f"✅ {ok_count} ta  ❌ {fail_count} ta\n\n"
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
        f"📊 *Yakuniy hisobot* ({len(users)} ta):",
        f"✅ Muvaffaqiyat: {ok_count}",
        f"❌ Xato: {fail_count}",
        "",
    ]
    for r in results:
        lines.append(r["message"])

    report = "\n".join(lines)
    if len(report) <= 4000:
        try:
            await status.edit_text(report, parse_mode="Markdown")
        except Exception:
            await status.edit_text(report)
    else:
        await status.edit_text(f"📊 *Hisobot*\n✅ {ok_count}  ❌ {fail_count}", parse_mode="Markdown")
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

    gmail_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(btn_connect_gmail, pattern="^(connect_gmail|change_gmail)$"),
        ],
        states={
            ASK_EMAIL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
            ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(gmail_conv)
    app.add_handler(CallbackQueryHandler(btn_reset_counter, pattern="^reset_counter$"))
    app.add_handler(CallbackQueryHandler(btn_help, pattern="^help$"))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Bot ishga tushdi ✅")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
