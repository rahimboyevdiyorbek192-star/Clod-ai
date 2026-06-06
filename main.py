import os
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from modules import chatbot, threat_analyzer, screenshot_analyzer

app = FastAPI(title="Clod-AI Cybersecurity Platform", version="2.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

SUPPORTED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


def _require_api_key():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY sozlanmagan")


@app.get("/")
def index():
    return FileResponse("static/index.html")


# ── Cybersecurity Chatbot ─────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    messages: list[dict]


@app.post("/api/chat")
def chat(req: ChatRequest):
    _require_api_key()
    reply = chatbot.chat(req.messages)
    return {"reply": reply}


# ── Threat Text Analyzer ──────────────────────────────────────────────────────

class TextRequest(BaseModel):
    text: str


@app.post("/api/analyze-threat")
def analyze_threat(req: TextRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Matn bo'sh bo'lmasligi kerak")
    return threat_analyzer.analyze(req.text)


# ── Security Screenshot Analyzer ──────────────────────────────────────────────

@app.post("/api/analyze-screenshot")
async def analyze_screenshot(file: UploadFile = File(...)):
    if file.content_type not in SUPPORTED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Faqat PNG, JPEG, WEBP, GIF qabul qilinadi")
    _require_api_key()
    data = await file.read()
    analysis = screenshot_analyzer.analyze(data, media_type=file.content_type)
    return {"analysis": analysis}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
