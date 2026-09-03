import openpyxl
from io import BytesIO

FIELD_ALIASES = {
    "email": ["email", "e-mail", "pochta", "email manzil"],
    "ism": ["ism", "first name", "name", "ismi"],
    "familiya": ["familiya", "last name", "surname", "familiyasi"],
    "parol": ["parol", "password", "pass"],
    "promo": ["promo", "promo kod", "promokod", "referral", "code"],
}


def _match_header(header: str) -> str | None:
    h = header.strip().lower()
    for field, aliases in FIELD_ALIASES.items():
        if h in aliases:
            return field
    return None


def parse_excel(file_bytes: bytes) -> list[dict]:
    """
    Excel fayldan foydalanuvchilar ro'yxatini o'qiydi.

    Sarlavha ustunlari (ixtiyoriy tartibda):
        ism, familiya, parol, [email], [promo]

    Email ustuni bo'lmasa ham ishlaydi — bot o'zi alias yaratadi.
    Birinchi qator sarlavha yoki ma'lumot bo'lishi mumkin (avtomatik aniqlanadi).
    """
    wb = openpyxl.load_workbook(BytesIO(file_bytes), data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    # Birinchi qator sarlavhami tekshirish
    first = [str(c).strip() if c is not None else "" for c in rows[0]]
    header_map: dict[int, str] = {}
    for col_idx, cell in enumerate(first):
        field = _match_header(cell)
        if field:
            header_map[col_idx] = field

    has_headers = bool(header_map)
    data_rows = rows[1:] if has_headers else rows

    # Sarlavha yo'q bo'lsa: A=ism, B=familiya, C=parol, D=promo (email yo'q)
    positional_no_email = ["ism", "familiya", "parol", "promo"]

    users: list[dict] = []
    for row in data_rows:
        cells = [str(c).strip() if c is not None else "" for c in row]
        if not cells or not any(cells):
            continue

        if has_headers:
            user: dict = {"email": "", "ism": "", "familiya": "", "parol": "", "promo": ""}
            for col_idx, field in header_map.items():
                if col_idx < len(cells):
                    user[field] = cells[col_idx]
        else:
            user = {
                positional_no_email[i]: cells[i] if i < len(cells) else ""
                for i in range(len(positional_no_email))
            }
            user.setdefault("email", "")

        # Ism va parol majburiy
        if user.get("ism") and user.get("parol"):
            users.append(user)

    return users


def has_email_column(users: list[dict]) -> bool:
    """Excel da email ustuni bor-yo'qligini tekshirish."""
    return any(u.get("email") and "@" in u["email"] for u in users)
