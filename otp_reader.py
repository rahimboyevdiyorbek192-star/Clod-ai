import asyncio
import email as email_lib
import imaplib
import logging
import re
import time

logger = logging.getLogger(__name__)

IMAP_SERVERS = {
    "gmail.com": "imap.gmail.com",
    "mail.ru": "imap.mail.ru",
    "yandex.ru": "imap.yandex.ru",
    "yandex.com": "imap.yandex.ru",
    "yahoo.com": "imap.mail.yahoo.com",
    "outlook.com": "outlook.office365.com",
    "hotmail.com": "outlook.office365.com",
}


def get_imap_server(email_addr: str) -> str:
    domain = email_addr.split("@")[-1].lower()
    return IMAP_SERVERS.get(domain, f"imap.{domain}")


def _extract_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct in ("text/plain", "text/html"):
                try:
                    return part.get_payload(decode=True).decode("utf-8", errors="ignore")
                except Exception:
                    pass
    try:
        return msg.get_payload(decode=True).decode("utf-8", errors="ignore")
    except Exception:
        return str(msg.get_payload())


async def read_otp_from_imap(
    email_addr: str,
    imap_password: str,
    imap_server: str | None = None,
    timeout: int = 120,
) -> str | None:
    """
    Poll IMAP inbox for a 4-digit OTP from ustoz.ai.
    Returns the OTP string or None if not found within timeout seconds.
    """
    if not imap_server:
        imap_server = get_imap_server(email_addr)

    deadline = time.time() + timeout
    today = time.strftime("%d-%b-%Y")

    while time.time() < deadline:
        try:
            mail = imaplib.IMAP4_SSL(imap_server, timeout=10)
            mail.login(email_addr, imap_password)
            mail.select("inbox")

            # Search unseen emails from ustoz today
            _, ids = mail.search(None, f'(SINCE "{today}" FROM "ustoz")')
            if not ids[0]:
                # Broader search
                _, ids = mail.search(None, f'(SINCE "{today}")')

            if ids[0]:
                all_ids = ids[0].split()
                for msg_id in reversed(all_ids[-10:]):
                    _, data = mail.fetch(msg_id, "(RFC822)")
                    for part in data:
                        if not isinstance(part, tuple):
                            continue
                        msg = email_lib.message_from_bytes(part[1])
                        sender = msg.get("From", "")
                        subject = msg.get("Subject", "")

                        # Only process emails related to ustoz.ai
                        if "ustoz" in sender.lower() or "ustoz" in subject.lower() or "tasdiqlash" in subject.lower():
                            body = _extract_body(msg)
                            match = re.search(r'\b(\d{4})\b', body)
                            if match:
                                mail.logout()
                                return match.group(1)

            mail.logout()

        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP auth error for {email_addr}: {e}")
            return None  # Wrong credentials — stop immediately
        except Exception as e:
            logger.warning(f"IMAP error for {email_addr}: {e}")

        await asyncio.sleep(5)

    return None
