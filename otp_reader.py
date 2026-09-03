"""
IMAP orqali ustoz.ai OTP kodini o'qiydi.

Muhim: registration_start_time parametri orqali faqat ro'yxatdan o'tish
BOSHLANGANDAN KEYIN kelgan emaillardan OTP qidiriladi — eski OTP lar
bilan chalkashish oldini oladi.
"""

import asyncio
import email as email_lib
import email.utils
import imaplib
import logging
import re
import time

logger = logging.getLogger(__name__)


def _extract_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() in ("text/plain", "text/html"):
                try:
                    return part.get_payload(decode=True).decode("utf-8", errors="ignore")
                except Exception:
                    pass
    try:
        return msg.get_payload(decode=True).decode("utf-8", errors="ignore")
    except Exception:
        return str(msg.get_payload())


def _email_received_time(msg) -> float:
    """Email kelgan vaqtni Unix timestamp sifatida qaytaradi."""
    date_str = msg.get("Date", "")
    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed.timestamp()
    except Exception:
        return 0.0


async def read_otp_from_imap(
    imap_email: str,
    imap_password: str,
    imap_server: str = "imap.gmail.com",
    registration_start_time: float | None = None,
    timeout: int = 90,
) -> str | None:
    """
    Gmail inboxdan ustoz.ai OTP sini o'qiydi.

    registration_start_time — shu vaqtdan KEYIN kelgan email lar
    ichidan OTP qidiriladi. Bir nechta ketma-ket ro'yxatdan o'tishda
    eski OTP bilan chalkashishni oldini oladi.

    Returns:
        4 xonali OTP string yoki None (timeout bo'lsa)
    """
    if registration_start_time is None:
        registration_start_time = time.time() - 10  # 10 son tolerance

    deadline = time.time() + timeout
    today = time.strftime("%d-%b-%Y")

    while time.time() < deadline:
        try:
            mail = imaplib.IMAP4_SSL(imap_server, timeout=15)
            mail.login(imap_email, imap_password)
            mail.select("inbox")

            # Bugungi emaillarni ol
            _, ids = mail.search(None, f'(SINCE "{today}")')

            if ids[0]:
                all_ids = ids[0].split()

                # Oxirgi 20 ta emailni tekshir (eng yangilarini)
                for msg_id in reversed(all_ids[-20:]):
                    _, data = mail.fetch(msg_id, "(RFC822)")
                    for part in data:
                        if not isinstance(part, tuple):
                            continue

                        msg = email_lib.message_from_bytes(part[1])

                        # Faqat ro'yxatdan o'tish boshlanganidan KEYIN kelgan emaillar
                        received_time = _email_received_time(msg)
                        if received_time < registration_start_time:
                            continue

                        sender = msg.get("From", "").lower()
                        subject = msg.get("Subject", "").lower()

                        is_ustoz = (
                            "ustoz" in sender
                            or "ustoz" in subject
                            or "tasdiqlash" in subject
                            or "verification" in subject
                            or "confirm" in subject
                            or "otp" in subject
                            or "kod" in subject
                        )

                        if not is_ustoz:
                            continue

                        body = _extract_body(msg)

                        # 4 xonali raqam qidirish
                        # Ustoz.ai emailida kod odatda alohida qatorda turadi
                        matches = re.findall(r'\b(\d{4})\b', body)
                        if matches:
                            mail.logout()
                            # Birinchi 4 xonali raqamni qaytaramiz
                            return matches[0]

            mail.logout()

        except imaplib.IMAP4.error as exc:
            logger.error(f"IMAP xatolik (login/server): {exc}")
            return None  # Noto'g'ri parol — to'xtatish
        except Exception as exc:
            logger.warning(f"IMAP ulanish xatoligi: {exc}")

        await asyncio.sleep(5)

    return None
