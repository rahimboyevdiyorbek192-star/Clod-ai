# Clod-AI Platform

Uchta AI qobiliyatini birlashtirgan veb platforma:

| Modul | Texnologiya | Vazifa |
|---|---|---|
| 💬 **Chatbot** | Claude API (Haiku) | O'zbek/rus/ingliz tillarida suhbat |
| 🖼️ **Rasm tasnifi** | ResNet-50 (ImageNet) | Rasmni 1000 ta sinfdan biriga ajratish |
| 📝 **Matn tahlili** | DistilBERT + BERT-NER | His-tuyg'u + shaxs/joy/tashkilot aniqlash |

## O'rnatish

```bash
pip install -r requirements.txt
```

## Ishga tushirish

```bash
export ANTHROPIC_API_KEY="your-key-here"
python main.py
```

Brauzerda oching: `http://localhost:8000`

## Loyiha tuzilmasi

```
Clod-ai/
├── main.py                  # FastAPI server
├── modules/
│   ├── chatbot.py           # Claude API integratsiyasi
│   ├── image_classifier.py  # ResNet-50 tasniflovchi
│   └── text_analyzer.py     # DistilBERT/BERT-NER tahlillovchi
├── static/
│   └── index.html           # Veb interfeys
└── requirements.txt
```

## API endpointlari

| Method | URL | Tavsif |
|---|---|---|
| POST | `/api/chat` | `{"messages": [...]}` — chatbot |
| POST | `/api/classify-image` | `multipart/form-data` — rasm tasnifi |
| POST | `/api/analyze-text` | `{"text": "..."}` — matn tahlili |
