import os
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from modules import chatbot, image_classifier, text_analyzer

app = FastAPI(title="Clod-AI Platform", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")


# ── Chatbot ──────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    messages: list[dict]


@app.post("/api/chat")
def chat(req: ChatRequest):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY sozlanmagan")
    reply = chatbot.chat(req.messages)
    return {"reply": reply}


# ── Image classifier ─────────────────────────────────────────────────────────

@app.post("/api/classify-image")
async def classify_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Faqat rasm fayllari qabul qilinadi")
    data = await file.read()
    results = image_classifier.classify(data)
    return {"predictions": results}


# ── Text analyzer ────────────────────────────────────────────────────────────

class TextRequest(BaseModel):
    text: str


@app.post("/api/analyze-text")
def analyze_text(req: TextRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Matn bo'sh bo'lmasligi kerak")
    result = text_analyzer.analyze(req.text)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
