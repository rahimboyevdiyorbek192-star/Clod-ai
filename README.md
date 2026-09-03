# Ustoz.ai Avtomatik Ro'yxatdan O'tkazish Boti

Excel fayldan foydalanib, ustoz.ai saytiga avtomatik ro'yxatdan o'tkazadi.

## O'rnatish

```bash
pip install -r requirements.txt
playwright install chromium
```

## Sozlash

`.env.example` nusxasini `.env` ga ko'chiring va token kiriting:

```bash
cp .env.example .env
```

`.env` faylini oching va `BOT_TOKEN` ga Telegram bot tokenini yozing.

## Ishga tushurish

```bash
python bot.py
```

## Excel fayl formati

Birinchi qator sarlavha bo'lishi kerak:

| email | ism | familiya | parol | imap_parol | promo |
|-------|-----|----------|-------|------------|-------|
| user@gmail.com | Ali | Valiyev | Parol123! | gmail-app-paroli | (ixtiyoriy) |

### imap_parol nima?

Gmail App Password — bu Gmail uchun maxsus 16 belgili parol:

1. Gmail → **Sozlamalar** → **Xavfsizlik**
2. **2-bosqichli tasdiqlash** ni yoqing
3. **App Passwords** → yangi parol yarating
4. 16 belgili parolni Excel ga `imap_parol` ustuniga kiriting

### Ro'yxatdan o'tish jarayoni (avtomatik)

1. Bot emailni ustoz.ai ga kiritadi
2. Shaxsiy ma'lumotlarni to'ldiradi
3. Emailga kelgan 4 raqamli OTP ni IMAP orqali o'qiydi
4. OTP kiritadi va ro'yxatdan o'tishni tugatadi
5. Natijani Telegram ga yuboradi
