import re

# IOC extraction patterns
_IP = re.compile(r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b')
_URL = re.compile(r'https?://[^\s<>"\']+|www\.[^\s<>"\']+', re.I)
_EMAIL = re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b')
_MD5 = re.compile(r'\b[a-fA-F0-9]{32}\b')
_SHA1 = re.compile(r'\b[a-fA-F0-9]{40}\b')
_SHA256 = re.compile(r'\b[a-fA-F0-9]{64}\b')
_CVE = re.compile(r'CVE-\d{4}-\d{4,7}', re.I)

# Phishing heuristic keywords (English + Uzbek + Russian)
PHISHING_KEYWORDS = [
    # English
    "urgent", "immediately", "account suspended", "verify your", "click here",
    "confirm your", "update your", "login required", "security alert",
    "unusual activity", "limited time", "act now", "expires today",
    "your account will be", "reset your password", "unauthorized access",
    # Uzbek
    "shoshiling", "zudlik bilan", "hisobingiz", "tasdiqlang", "kirish talab",
    "xavfsizlik ogohlantirishi", "muddati tugaydi", "bloklangan",
    # Russian
    "срочно", "немедленно", "ваш аккаунт", "подтвердите", "заблокирован",
    "необычная активность", "истекает",
]

# Log-based attack signatures
ATTACK_PATTERNS = {
    "SQL Injection": re.compile(
        r"('|\"|--|#|/\*|\bOR\b\s+\d+=\d+|\bAND\b\s+\d+=\d+|"
        r"UNION\s+SELECT|DROP\s+TABLE|INSERT\s+INTO|SELECT\s+\*\s+FROM|"
        r"SLEEP\s*\(|BENCHMARK\s*\(|LOAD_FILE\s*\()",
        re.I,
    ),
    "XSS": re.compile(
        r"<script|javascript:|onerror\s*=|onload\s*=|alert\s*\(|"
        r"document\.cookie|<img[^>]+src\s*=\s*[\"']?javascript:",
        re.I,
    ),
    "Path Traversal": re.compile(
        r"\.\./|\.\.\\|%2e%2e%2f|%252e%252e|/etc/passwd|/etc/shadow|"
        r"\\windows\\system32",
        re.I,
    ),
    "Command Injection": re.compile(
        r";\s*(ls|cat|pwd|id|whoami|wget|curl|bash|sh|nc|netcat|python|perl)\b"
        r"|\|\s*(ls|cat|id|whoami)\b"
        r"|`[^`]+`|\$\([^)]+\)",
        re.I,
    ),
    "Brute Force": re.compile(
        r"(failed|invalid|incorrect|wrong)\s+(login|password|credentials|auth)"
        r"|authentication\s+failure|too\s+many\s+(attempts|requests)",
        re.I,
    ),
    "SSRF": re.compile(
        r"(169\.254\.169\.254|localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0)"
        r"|(file|gopher|dict|ftp)://",
        re.I,
    ),
    "LFI/RFI": re.compile(
        r"(include|require|include_once|require_once)\s*\([^)]*\.\.(\/|\\)"
        r"|\.(php|asp|jsp)\?[^&]*=(https?://|//)",
        re.I,
    ),
}

THREAT_LEVEL = {0: "Xavfsiz", 1: "Past", 2: "O'rta", 3: "Yuqori", 4: "Kritik"}
THREAT_COLOR = {0: "safe", 1: "low", 2: "medium", 3: "high", 4: "critical"}


def _extract_iocs(text: str) -> dict:
    return {
        "ips": sorted(set(_IP.findall(text))),
        "urls": sorted(set(_URL.findall(text))),
        "emails": sorted(set(_EMAIL.findall(text))),
        "hashes": {
            "md5": sorted(set(_MD5.findall(text))),
            "sha1": sorted(set(_SHA1.findall(text))),
            "sha256": sorted(set(_SHA256.findall(text))),
        },
        "cves": sorted(set(_CVE.findall(text))),
    }


def _phishing_score(text: str) -> dict:
    lower = text.lower()
    matched = [kw for kw in PHISHING_KEYWORDS if kw in lower]
    score = min(len(matched) * 14, 98)
    level = "Yuqori" if score >= 56 else "O'rta" if score >= 28 else "Past"
    return {"score": score, "level": level, "keywords": matched}


def _detect_attacks(text: str) -> list[str]:
    return [name for name, pat in ATTACK_PATTERNS.items() if pat.search(text)]


def analyze(text: str) -> dict:
    iocs = _extract_iocs(text)
    phishing = _phishing_score(text)
    attacks = _detect_attacks(text)

    total_iocs = (
        len(iocs["ips"]) + len(iocs["urls"]) + len(iocs["emails"])
        + len(iocs["hashes"]["md5"]) + len(iocs["hashes"]["sha1"])
        + len(iocs["hashes"]["sha256"]) + len(iocs["cves"])
    )

    # Threat level: 0-4
    level_idx = 0
    if attacks:
        level_idx = max(level_idx, 3)
    if phishing["score"] >= 56:
        level_idx = max(level_idx, 3)
    elif phishing["score"] >= 28:
        level_idx = max(level_idx, 2)
    if total_iocs >= 5:
        level_idx = max(level_idx, 2)
    elif total_iocs >= 1:
        level_idx = max(level_idx, 1)
    if attacks and total_iocs >= 3:
        level_idx = 4

    return {
        "iocs": iocs,
        "total_iocs": total_iocs,
        "phishing": phishing,
        "attack_patterns": attacks,
        "threat_level": THREAT_LEVEL[level_idx],
        "threat_color": THREAT_COLOR[level_idx],
        "word_count": len(text.split()),
    }
