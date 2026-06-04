import io
import json
import urllib.request
from pathlib import Path

import torch
import torchvision.transforms as transforms
from PIL import Image
from torchvision.models import resnet50, ResNet50_Weights

_model = None
_labels = None

LABELS_URL = (
    "https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/"
    "master/imagenet-simple-labels.json"
)
LABELS_CACHE = Path(__file__).parent / "imagenet_labels.json"

TRANSFORM = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def _load_labels() -> list[str]:
    global _labels
    if _labels is not None:
        return _labels
    if LABELS_CACHE.exists():
        _labels = json.loads(LABELS_CACHE.read_text())
    else:
        with urllib.request.urlopen(LABELS_URL, timeout=10) as r:
            _labels = json.loads(r.read().decode())
        LABELS_CACHE.write_text(json.dumps(_labels))
    return _labels


def _load_model():
    global _model
    if _model is None:
        _model = resnet50(weights=ResNet50_Weights.DEFAULT)
        _model.eval()
    return _model


def classify(image_bytes: bytes, top_k: int = 5) -> list[dict]:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = TRANSFORM(img).unsqueeze(0)

    model = _load_model()
    labels = _load_labels()

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)[0]

    top_probs, top_indices = torch.topk(probs, top_k)
    return [
        {"label": labels[idx.item()], "confidence": round(prob.item() * 100, 2)}
        for prob, idx in zip(top_probs, top_indices)
    ]
