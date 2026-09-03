import openpyxl
from io import BytesIO

FIELD_ALIASES = {
    "email":    ["email", "e-mail", "pochta", "email manzil", "mail"],
    "ism":      ["ism", "first name", "name", "ismi", "firstname"],
    "familiya": ["familiya", "last name", "surname", "familiyasi", "lastname"],
    "parol":    ["parol", "password", "pass", "kalit"],
    "promo":    ["promo", "promo kod", "promokod", "referral", "code"],
}

REQUIRED_FIELDS = ["ism", "familiya", "parol"]


def _match_header(header: str) -> str | None:
    h = header.strip().lower()
    for field, aliases in FIELD_ALIASES.items():
        if h in aliases:
            return field
    return None


def parse_excel(file_bytes: bytes) -> tuple[list[dict], list[str]]:
    """
    Excel fayldan foydalanuvchilar ro'yxatini o'qiydi.

    Returns:
        (users, errors) — users: to'g'ri qatorlar, errors: xatoliklar ro'yxati

    Sarlavha ustunlari (ixtiyoriy tartibda):
        ism, familiya, parol — majburiy
        email, promo        — ixtiyoriy

    Email yo'q bo'lsa, bot o'zi alias yaratadi.
    Faqat .xlsx qo'llab-quvvatlanadi.
    """
    wb = openpyxl.load_workbook(BytesIO(file_bytes), data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], ["Excel fayl bo'sh!"]

    # Sarlavha qatori aniqlash
    first = [str(c).strip() if c is not None else "" for c in rows[0]]
    header_map: dict[int, str] = {}
    for col_idx, cell in enumerate(first):
        field = _match_header(cell)
        if field:
            header_map[col_idx] = field

    has_headers = bool(header_map)
    data_rows = rows[1:] if has_headers else rows

    # Sarlavhasiz Excel: A=ism, B=familiya, C=parol, D=promo
    positional = ["ism", "familiya", "parol", "promo"]

    users: list[dict] = []
    errors: list[str] = []

    for row_num, row in enumerate(data_rows, start=2 if has_headers else 1):
        cells = [str(c).strip() if c is not None else "" for c in row]
        if not cells or not any(c for c in cells):
            continue

        if has_headers:
            user: dict = {f: "" for f in ["email", "ism", "familiya", "parol", "promo"]}
            for col_idx, field in header_map.items():
                if col_idx < len(cells):
                    user[field] = cells[col_idx]
        else:
            user = {
                positional[i]: cells[i] if i < len(cells) else ""
                for i in range(len(positional))
            }
            user.setdefault("email", "")

        # Majburiy maydonlarni tekshirish
        missing = [f for f in REQUIRED_FIELDS if not user.get(f)]
        if missing:
            errors.append(f"Qator {row_num}: {', '.join(missing)} bo'sh")
            continue

        # Parol minimal uzunligi
        if len(user.get("parol", "")) < 6:
            errors.append(f"Qator {row_num} ({user.get('ism')}): parol kamida 6 ta belgi bo'lishi kerak")
            continue

        users.append(user)

    return users, errors


def has_email_column(users: list[dict]) -> bool:
    """Excel da email ustuni bor-yo'qligini tekshiradi."""
    return any(u.get("email") and "@" in u["email"] for u in users)
