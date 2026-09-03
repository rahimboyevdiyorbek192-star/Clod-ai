import asyncio
import email as email_lib
import imaplib
import logging
import re
import time

logger = logging.getLogger(__name__)


def _extract_body(msg) -> str:
    """Email message dan matn olish."""
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


async def read_otp_from_imap(
    imap_email: str,
    imap_password: str,
    imap_server: str = "imap.gmail.com",
    timeout: int = 90,
) -> str | None:
    """
    Bitta Gmail inboxdan ustoz.ai OTP sini o'qiydi.
    Oxirgi kelgan OTP emailni topadi (alias emaillarning barchasi shu inboxga keladi).

    Returns:
        4 raqamli OTP string yoki None
    """
    deadline = time.time() + timeout
    today = time.strftime("%d-%b-%Y")
    last_seen_id: bytes | None = None

    while time.time() < deadline:
        try:
            mail = imaplib.IMAP4_SSL(imap_server, timeout=15)
            mail.login(imap_email, imap_password)
            mail.select("inbox")

            # Bugungi, ustoz.ai dan kelgan emaillarni qidirish
            _, ids = mail.search(None, f'(SINCE "{today}" FROM "ustoz")')
            if not ids[0]:
                _, ids = mail.search(None, f'(SINCE "{today}")')

            if ids[0]:
                all_ids = ids[0].split()
                # Eng so'nggi emailni ol
                latest_id = all_ids[-1]

                # Avval ko'rilgan email bo'lsa, yangi email kelishini kut
                if last_seen_id == latest_id:
                    mail.logout()
                    await asyncio.sleep(5)
                    continue

                _, data = mail.fetch(latest_id, "(RFC822)")
                for part in data:
                    if not isinstance(part, tuple):
                        continue
                    msg = email_lib.message_from_bytes(part[1])
                    sender = msg.get("From", "").lower()
                    subject = msg.get("Subject", "").lower()

                    is_ustoz = (
                        "ustoz" in sender
                        or "ustoz" in subject
                        or "tasdiqlash" in subject
                        or "verification" in subject
                        or "otp" in subject
                    )

                    if is_ustoz:
                        body = _extract_body(msg)
                        match = re.search(r'\b(\d{4})\b', body)
                        if match:
                            mail.logout()
                            return match.group(1)

                last_seen_id = latest_id

            mail.logout()

        except imaplib.IMAP4.error as exc:
            logger.error(f"IMAP xatolik (login yoki server): {exc}")
            return None
        except Exception as exc:
            logger.warning(f"IMAP ulanish xatoligi: {exc}")

        await asyncio.sleep(5)

    return None
