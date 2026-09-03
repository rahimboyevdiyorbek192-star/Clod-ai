"""
ustoz.ai da Playwright orqali avtomatik ro'yxatdan o'tkazish.

Screenshot orqali tekshirilgan URL va selector strategiyasi:
  - Login: ustoz.ai/login  (screenshot 1)
  - Signup: ustoz.ai/signup?type=... (screenshot 2)
  - OTP:    ustoz.ai/signup/otp?s=... (screenshot 3)
"""

import asyncio
import logging
import time
from typing import Callable, Awaitable

from playwright.async_api import async_playwright, Page, TimeoutError as PWTimeout

from otp_reader import read_otp_from_imap

logger = logging.getLogger(__name__)

StatusCb = Callable[[str], Awaitable[None]]

BASE = "https://ustoz.ai"


async def _safe_notify(cb: StatusCb | None, msg: str):
    if cb:
        try:
            await cb(msg)
        except Exception:
            pass


async def _click_continue(page: Page):
    """'Davom etish' tugmasini topib bosadi (bir necha selector sinab ko'radi)."""
    selectors = [
        'button:has-text("Davom etish")',
        'button:has-text("davom")',
        'button[type="submit"]',
        'button.btn-primary',
        'button:last-of-type',
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=2000):
                await btn.click()
                return
        except Exception:
            continue
    raise RuntimeError("'Davom etish' tugmasi topilmadi")


async def _fill_email_field(page: Page, email: str):
    """Email input ni topib to'ldiradi."""
    selectors = [
        'input[type="email"]',
        'input[placeholder="Email"]',
        'input[placeholder*="mail" i]',
        'input[name="email"]',
        'input[id*="email" i]',
    ]
    for sel in selectors:
        try:
            inp = page.locator(sel).first
            if await inp.is_visible(timeout=2000):
                await inp.fill(email)
                return
        except Exception:
            continue
    raise RuntimeError("Email input topilmadi")


async def _wait_for_url_pattern(page: Page, pattern: str, timeout_ms: int = 20000):
    """URL o'zgarishini kutadi. Agar URL o'zgarmasa, sahifada xato bormi tekshiradi."""
    try:
        await page.wait_for_url(f"**{pattern}**", timeout=timeout_ms)
    except PWTimeout:
        # Xato xabarini qaytarish
        err = ""
        try:
            for sel in ['[class*="error" i]', '[role="alert"]', '.text-red-500', '[class*="danger" i]']:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1000):
                    err = (await el.inner_text()).strip()
                    break
        except Exception:
            pass
        raise RuntimeError(
            f"URL '{pattern}' ga o'tish vaqti tugadi. "
            + (f"Sahifa xatosi: {err}" if err else "Sahifada xato bo'lishi mumkin.")
        )


async def register_user(
    email: str,
    ism: str,
    familiya: str,
    parol: str,
    promo: str = "",
    imap_email: str = "",
    imap_password: str = "",
    imap_server: str = "imap.gmail.com",
    status_cb: StatusCb | None = None,
) -> dict:
    """
    ustoz.ai da bir foydalanuvchini ro'yxatdan o'tkazadi.

    Returns:
        {"success": bool, "email": str, "message": str}
    """
    if not imap_email or not imap_password:
        return {
            "success": False,
            "email": email,
            "message": "❌ Gmail ulanmagan! /start → 'Gmail ulash' tugmasini bosing.",
        }

    async def notify(msg: str):
        await _safe_notify(status_cb, msg)
        logger.info(f"[{email}] {msg}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/16.0 Mobile/15E148 Safari/604.1"
            ),
        )
        page = await ctx.new_page()

        try:
            # ── STEP 1: Login sahifasi — email kiriting ───────────────────
            await notify("🌐 ustoz.ai ga ulanilmoqda...")
            await page.goto(f"{BASE}/login", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # "Email" tab ni bosish (agar Telefon tab default bo'lsa)
            try:
                for tab_text in ["Email", "email"]:
                    tab = page.locator(f"text={tab_text}").first
                    if await tab.is_visible(timeout=2000):
                        await tab.click()
                        await asyncio.sleep(0.4)
                        break
            except Exception:
                pass

            await _fill_email_field(page, email)
            await asyncio.sleep(0.3)
            await _click_continue(page)

            # ── STEP 2: Shaxsiy ma'lumotlar (/signup?type=...) ───────────
            await notify("📝 Shaxsiy ma'lumotlar to'ldirilmoqda...")
            await _wait_for_url_pattern(page, "/signup", timeout_ms=20000)
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Ism
            ism_selectors = [
                'input[placeholder="Ism"]',
                'input[placeholder*="ism" i]',
                'input[name="firstName"]',
                'input[name="first_name"]',
                'input[id*="ism" i]',
            ]
            for sel in ism_selectors:
                try:
                    inp = page.locator(sel).first
                    if await inp.is_visible(timeout=2000):
                        await inp.fill(ism)
                        break
                except Exception:
                    continue

            # Familiya
            familiya_selectors = [
                'input[placeholder="Familiya"]',
                'input[placeholder*="familiya" i]',
                'input[name="lastName"]',
                'input[name="last_name"]',
                'input[id*="familiya" i]',
            ]
            for sel in familiya_selectors:
                try:
                    inp = page.locator(sel).first
                    if await inp.is_visible(timeout=2000):
                        await inp.fill(familiya)
                        break
                except Exception:
                    continue

            # Parol (ikkita password input)
            pwd_inputs = page.locator('input[type="password"]')
            pwd_count = await pwd_inputs.count()
            if pwd_count >= 2:
                await pwd_inputs.nth(0).fill(parol)
                await pwd_inputs.nth(1).fill(parol)
            elif pwd_count == 1:
                await pwd_inputs.nth(0).fill(parol)

            # Promo (ixtiyoriy)
            if promo:
                try:
                    promo_inp = page.locator(
                        'input[placeholder*="promo" i], input[placeholder*="Promo"]'
                    ).first
                    if await promo_inp.is_visible(timeout=2000):
                        await promo_inp.fill(promo)
                except Exception:
                    pass

            # Ro'yxatdan o'tish boshlanayotgan vaqtni saqlaymiz (OTP uchun)
            registration_start_time = time.time()

            await _click_continue(page)

            # ── STEP 3: OTP (/signup/otp?s=...) ──────────────────────────
            await notify("⏳ OTP kodi kutilmoqda...")
            await _wait_for_url_pattern(page, "/otp", timeout_ms=20000)

            otp = await read_otp_from_imap(
                imap_email=imap_email,
                imap_password=imap_password,
                imap_server=imap_server,
                registration_start_time=registration_start_time,
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

            # 4 ta alohida raqam qutisi
            digit_inputs = page.locator('input[maxlength="1"]')
            digit_count = await digit_inputs.count()

            if digit_count >= 4:
                for i, digit in enumerate(otp[:4]):
                    await digit_inputs.nth(i).fill(digit)
                    await asyncio.sleep(0.15)
            else:
                # Yagona input fallback
                for sel in ['input[type="number"]', 'input[type="tel"]', 'input[inputmode="numeric"]']:
                    try:
                        single = page.locator(sel).first
                        if await single.is_visible(timeout=2000):
                            await single.fill(otp)
                            break
                    except Exception:
                        continue

            await _click_continue(page)
            await asyncio.sleep(4)

            # ── Natija ────────────────────────────────────────────────────
            current_url = page.url
            if "/otp" not in current_url.lower():
                return {
                    "success": True,
                    "email": email,
                    "message": f"✅ {email} — muvaffaqiyatli ro'yxatdan o'tdi!",
                }

            # OTP noto'g'ri bo'lsa xato xabarini ol
            err_text = ""
            try:
                for err_sel in ['[class*="error" i]', '[role="alert"]', '.text-red-500', '[class*="danger" i]']:
                    el = page.locator(err_sel).first
                    if await el.is_visible(timeout=1500):
                        err_text = (await el.inner_text()).strip()
                        break
            except Exception:
                pass

            return {
                "success": False,
                "email": email,
                "message": f"❌ {email}: OTP noto'g'ri. {err_text}".strip(),
            }

        except Exception as exc:
            logger.error(f"Xato: {email}", exc_info=True)
            return {
                "success": False,
                "email": email,
                "message": f"❌ {email}: {str(exc)[:200]}",
            }
        finally:
            await ctx.close()
            await browser.close()
