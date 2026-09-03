import asyncio
import logging
import os
from typing import Callable, Awaitable

from playwright.async_api import async_playwright, Page

from otp_reader import read_otp_from_imap

logger = logging.getLogger(__name__)

StatusCb = Callable[[str], Awaitable[None]]

IMAP_EMAIL = os.getenv("IMAP_EMAIL", "")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")


async def _click_continue(page: Page):
    btn = page.locator('button:has-text("Davom etish")').first
    await btn.wait_for(state="visible", timeout=10000)
    await btn.click()


async def register_user(
    email: str,
    ism: str,
    familiya: str,
    parol: str,
    promo: str = "",
    status_cb: StatusCb | None = None,
) -> dict:
    """
    ustoz.ai da foydalanuvchini ro'yxatdan o'tkazadi.
    OTP ni IMAP_EMAIL inboxidan avtomatik o'qiydi.

    Returns:
        {"success": bool, "email": str, "message": str}
    """

    async def notify(msg: str):
        if status_cb:
            try:
                await status_cb(msg)
            except Exception:
                pass
        logger.info(f"[{email}] {msg}")

    if not IMAP_EMAIL or not IMAP_PASSWORD:
        return {
            "success": False,
            "email": email,
            "message": "❌ IMAP_EMAIL yoki IMAP_PASSWORD .env da yo'q!",
        }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
            ),
        )
        page = await ctx.new_page()

        try:
            # ── STEP 1: Email ─────────────────────────────────────────────
            await notify("🌐 ustoz.ai ga ulanilmoqda...")
            await page.goto("https://ustoz.ai/login", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # Email tab bosish (agar Telefon tab ochiq bo'lsa)
            try:
                email_tab = page.locator("text=Email").first
                if await email_tab.is_visible(timeout=3000):
                    await email_tab.click()
                    await asyncio.sleep(0.3)
            except Exception:
                pass

            email_input = page.locator(
                'input[type="email"], '
                'input[placeholder*="mail" i], '
                'input[placeholder="Email"]'
            ).first
            await email_input.wait_for(state="visible", timeout=10000)
            await email_input.fill(email)
            await asyncio.sleep(0.3)

            await _click_continue(page)

            # ── STEP 2: Shaxsiy ma'lumotlar ──────────────────────────────
            await notify("📝 Ism, familiya, parol to'ldirilmoqda...")
            await page.wait_for_url("**/signup**", timeout=20000)
            await page.wait_for_load_state("networkidle", timeout=10000)

            await page.locator('input[placeholder="Ism"]').fill(ism)
            await page.locator('input[placeholder="Familiya"]').fill(familiya)

            pwd_inputs = page.locator('input[type="password"]')
            await pwd_inputs.nth(0).fill(parol)
            await pwd_inputs.nth(1).fill(parol)

            if promo:
                try:
                    promo_input = page.locator(
                        'input[placeholder*="promo" i], input[placeholder*="Promo"]'
                    ).first
                    if await promo_input.is_visible(timeout=2000):
                        await promo_input.fill(promo)
                except Exception:
                    pass

            await _click_continue(page)

            # ── STEP 3: OTP ───────────────────────────────────────────────
            await notify(f"⏳ OTP kodi kutilmoqda ({IMAP_EMAIL} inbox)...")
            await page.wait_for_url("**/otp**", timeout=20000)

            otp = await read_otp_from_imap(
                imap_email=IMAP_EMAIL,
                imap_password=IMAP_PASSWORD,
                imap_server=IMAP_SERVER,
                timeout=90,
            )

            if not otp:
                return {
                    "success": False,
                    "email": email,
                    "message": (
                        f"❌ {email}: OTP topilmadi (90 son kutildi).\n"
                        "Gmail App Password va IMAP sozlamalarini tekshiring."
                    ),
                }

            await notify(f"🔑 OTP {otp} kiritilmoqda...")

            # 4 alohida raqam qutisi
            digit_inputs = page.locator('input[maxlength="1"]')
            count = await digit_inputs.count()

            if count >= 4:
                for i, digit in enumerate(otp[:4]):
                    await digit_inputs.nth(i).fill(digit)
                    await asyncio.sleep(0.15)
            else:
                single = page.locator('input[type="number"], input[type="tel"], input').first
                await single.fill(otp)

            await _click_continue(page)
            await asyncio.sleep(4)

            # ── Natija ────────────────────────────────────────────────────
            url_now = page.url
            if "otp" not in url_now.lower():
                return {
                    "success": True,
                    "email": email,
                    "message": f"✅ {email} — muvaffaqiyatli ro'yxatdan o'tdi!",
                }

            err_text = ""
            try:
                err_el = page.locator(
                    '[class*="error" i], [class*="danger" i], .text-red-500, [role="alert"]'
                ).first
                if await err_el.is_visible(timeout=2000):
                    err_text = (await err_el.inner_text()).strip()
            except Exception:
                pass

            return {
                "success": False,
                "email": email,
                "message": f"❌ {email}: OTP noto'g'ri yoki muammo. {err_text}".strip(),
            }

        except Exception as exc:
            logger.error(f"Ro'yxatdan o'tishda xato: {email}", exc_info=True)
            return {
                "success": False,
                "email": email,
                "message": f"❌ {email}: Xato — {str(exc)[:200]}",
            }
        finally:
            await ctx.close()
            await browser.close()
