# Clod-AI | Kiberxavfsizlik Platformasi

Uchta kiberxavfsizlik AI modulini birlashtirgan veb platforma.

| Modul | Vazifa |
|---|---|
| 💬 **Chatbot** | CTF, zaifliklar, pentest, log tahlili bo'yicha mutaxassis |
| 🔍 **Tahdid Tahlili** | IOC ajratish, phishing aniqlash, hujum patternlari (SQL/XSS/RCE va h.k.) |
| 🖥️ **Skrinshot Tahlili** | Terminal, tarmoq diagrammasi, kod skrinshotini Claude Vision bilan tahlil |

## O'rnatish

```bash
pip install -r requirements.txt
```

## Ishga tushirish

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python main.py
# → http://localhost:8000
```

## API

| Method | Endpoint | Tavsif |
|---|---|---|
| POST | `/api/chat` | `{"messages":[...]}` — kiberxavfsizlik chatboti |
| POST | `/api/analyze-threat` | `{"text":"..."}` — IOC + phishing + hujum pattern tahlili |
| POST | `/api/analyze-screenshot` | `multipart` rasm — Claude Vision xavfsizlik tahlili |

## Loyiha tuzilmasi

```
Clod-ai/
├── main.py
├── modules/
│   ├── chatbot.py            # Claude Haiku — security expert chatbot
│   ├── threat_analyzer.py    # Regex IOC + phishing heuristics + attack patterns
│   └── screenshot_analyzer.py# Claude Haiku Vision — security screenshot analysis
├── static/index.html
└── requirements.txt
```

## Qo'llab-quvvatlanadigan tahdidlar

- SQL Injection, XSS, Path Traversal, Command Injection
- SSRF, LFI/RFI, Brute Force
- Phishing email tahlili (O'zbek + Ingliz + Rus)
- IOC: IP, URL, Email, MD5/SHA1/SHA256, CVE
