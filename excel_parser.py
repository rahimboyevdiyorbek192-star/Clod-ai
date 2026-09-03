import openpyxl
from io import BytesIO

FIELD_ALIASES = {
    "email": ["email", "e-mail", "pochta", "email manzil"],
    "ism": ["ism", "first name", "name", "ismi"],
    "familiya": ["familiya", "last name", "surname", "familiyasi"],
    "parol": ["parol", "password", "parol", "pass"],
    "imap_parol": ["imap_parol", "imap parol", "gmail parol", "app password", "imap password", "gmail app password"],
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
    Parse an Excel file and return a list of user dicts.

    Accepted column headers (case-insensitive):
        email, ism, familiya, parol, imap_parol, promo

    Falls back to positional columns (A=email, B=ism, C=familiya, D=parol, E=imap_parol, F=promo)
    if the first row does not look like headers.
    """
    wb = openpyxl.load_workbook(BytesIO(file_bytes), data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    # Detect whether the first row is a header row
    first = [str(c).strip() if c is not None else "" for c in rows[0]]
    header_map: dict[int, str] = {}

    for col_idx, cell in enumerate(first):
        field = _match_header(cell)
        if field:
            header_map[col_idx] = field

    has_headers = bool(header_map)
    data_rows = rows[1:] if has_headers else rows

    positional = ["email", "ism", "familiya", "parol", "imap_parol", "promo"]

    users: list[dict] = []
    for row in data_rows:
        cells = [str(c).strip() if c is not None else "" for c in row]
        if not cells or not cells[0]:
            continue

        if has_headers:
            user = {field: "" for field in positional}
            for col_idx, field in header_map.items():
                if col_idx < len(cells):
                    user[field] = cells[col_idx]
        else:
            user = {
                positional[i]: cells[i] if i < len(cells) else ""
                for i in range(len(positional))
            }

        if "@" in user.get("email", ""):
            users.append(user)

    return users
