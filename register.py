import asyncio
import logging
from typing import Callable, Awaitable

from playwright.async_api import async_playwright, Page

from otp_reader import read_otp_from_imap, get_imap_server

logger = logging.getLogger(__name__)

StatusCb = Callable[[str], Awaitable[None]]


async def _click_continue(page: Page):
    """Click the 'Davom etish' button."""
    btn = page.locator('button:has-text("Davom etish")').first
    await btn.wait_for(state="visible", timeout=10000)
    await btn.click()


async def register_user(
    email: str,
    ism: str,
    familiya: str,
    parol: str,
    promo: str = "",
    imap_password: str = "",
    imap_server: str | None = None,
    status_cb: StatusCb | None = None,
) -> dict:
    """
    Registers a single user on ustoz.ai via Playwright.

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

            # Activate Email tab (in case Phone tab is default)
            try:
                email_tab = page.locator("text=Email").first
                if await email_tab.is_visible(timeout=3000):
                    await email_tab.click()
                    await asyncio.sleep(0.3)
            except Exception:
                pass

            # Fill email field
            email_input = page.locator(
                'input[type="email"], '
                'input[placeholder*="mail" i], '
                'input[placeholder="Email"]'
            ).first
            await email_input.wait_for(state="visible", timeout=10000)
            await email_input.fill(email)
            await asyncio.sleep(0.3)

            await _click_continue(page)

            # ── STEP 2: Personal info ─────────────────────────────────────
            await notify("📝 Shaxsiy ma'lumotlar to'ldirilmoqda...")
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
            await notify("⏳ Tasdiqlash kodi (OTP) kutilmoqda...")
            await page.wait_for_url("**/otp**", timeout=20000)

            if not imap_password:
                return {
                    "success": False,
                    "email": email,
                    "message": f"⚠️ {email}: OTP sahifasiga yetildi, lekin IMAP parol yo'q. Excel ga imap_parol qo'shing.",
                }

            server = imap_server or get_imap_server(email)
            otp = await read_otp_from_imap(email, imap_password, server, timeout=90)

            if not otp:
                return {
                    "success": False,
                    "email": email,
                    "message": f"❌ {email}: OTP kodi topilmadi (90 son kutildi). IMAP sozlamalarini tekshiring.",
                }

            await notify(f"🔑 OTP: {otp} kiritilmoqda...")

            # Fill the 4 individual digit boxes
            digit_inputs = page.locator('input[maxlength="1"]')
            count = await digit_inputs.count()

            if count >= 4:
                for i, digit in enumerate(otp[:4]):
                    await digit_inputs.nth(i).fill(digit)
                    await asyncio.sleep(0.1)
            else:
                # Fallback: single combined input
                single = page.locator('input[type="number"], input[type="tel"], input').first
                await single.fill(otp)

            await _click_continue(page)
            await asyncio.sleep(4)

            # ── Check result ──────────────────────────────────────────────
            url_now = page.url
            if "otp" not in url_now.lower():
                return {
                    "success": True,
                    "email": email,
                    "message": f"✅ {email} — muvaffaqiyatli ro'yxatdan o'tdi!",
                }

            # Look for an error message on the page
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
                "message": f"❌ {email}: OTP noto'g'ri. {err_text or ''}".strip(),
            }

        except Exception as exc:
            logger.error(f"Error registering {email}", exc_info=True)
            short = str(exc)[:200]
            return {
                "success": False,
                "email": email,
                "message": f"❌ {email}: Xato — {short}",
            }
        finally:
            await ctx.close()
            await browser.close()
