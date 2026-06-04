from transformers import pipeline

_sentiment_pipe = None
_ner_pipe = None


def _get_sentiment():
    global _sentiment_pipe
    if _sentiment_pipe is None:
        _sentiment_pipe = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
        )
    return _sentiment_pipe


def _get_ner():
    global _ner_pipe
    if _ner_pipe is None:
        _ner_pipe = pipeline(
            "ner",
            model="dslim/bert-base-NER",
            aggregation_strategy="simple",
        )
    return _ner_pipe


LABEL_UZ = {
    "POSITIVE": "Ijobiy",
    "NEGATIVE": "Salbiy",
}


def analyze(text: str) -> dict:
    sentiment_result = _get_sentiment()(text[:512])[0]
    ner_results = _get_ner()(text[:512])

    entities = [
        {
            "text": e["word"],
            "type": e["entity_group"],
            "score": round(e["score"] * 100, 1),
        }
        for e in ner_results
    ]

    label_en = sentiment_result["label"]
    return {
        "sentiment": {
            "label_en": label_en,
            "label_uz": LABEL_UZ.get(label_en, label_en),
            "confidence": round(sentiment_result["score"] * 100, 2),
        },
        "entities": entities,
        "word_count": len(text.split()),
        "char_count": len(text),
    }
