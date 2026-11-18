"""Local, validated storage for customizable quick messages."""

import json
from pathlib import Path
from string import Formatter
from uuid import uuid4

from config import BASE_DIR, validate_message_text

TEMPLATES_FILE = BASE_DIR / "message_templates.json"
DEFAULT_TEMPLATES = [
    {"id": "hello", "title": "👋 Kendini tanıt", "text": "Merhaba {alici}, ben {ad}."},
    {"id": "available", "title": "💬 Müsait misin?", "text": "Merhaba {alici}, müsait olduğunda konuşabilir miyiz?"},
    {"id": "thanks", "title": "🙏 Teşekkür et", "text": "Çok teşekkür ederim {alici}!"},
]


def validate_text(text):
    validate_message_text(text)
    try:
        for _, field, spec, conversion in Formatter().parse(text):
            if field is not None and (field not in {"ad", "alici"} or spec or conversion):
                raise ValueError("Yalnızca {ad} ve {alici} alanlarını kullanın.")
    except ValueError as error:
        raise ValueError("Geçersiz mesaj alanı. {ad}, {alici}; düz süslü parantez için {{ ve }} kullanın.") from error


def make_template(title, text, template_id=None):
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Mesaj başlığı boş olamaz.")
    validate_text(text)
    return {"id": template_id or uuid4().hex, "title": title.strip(), "text": text.strip()}


def validate_templates(items):
    if not isinstance(items, list):
        raise ValueError("Hazır mesaj dosyası bir liste içermeli.")
    result, ids = [], set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ValueError("Geçersiz hazır mesaj kaydı.")
        if item["id"] in ids:
            raise ValueError("Hazır mesaj kimlikleri benzersiz olmalı.")
        ids.add(item["id"])
        result.append(make_template(item.get("title"), item.get("text"), item["id"]))
    return result


def load_templates(path=TEMPLATES_FILE):
    path = Path(path)
    if not path.exists():
        return [dict(item) for item in DEFAULT_TEMPLATES]
    return validate_templates(json.loads(path.read_text(encoding="utf-8")))


def save_templates(items, path=TEMPLATES_FILE):
    items = validate_templates(items)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def render_message(text, sender, recipient):
    validate_text(text)
    if not recipient.strip():
        raise ValueError("Önce alıcı adını girin.")
    fields = {field for _, field, _, _ in Formatter().parse(text) if field is not None}
    if "ad" in fields and not sender.strip():
        raise ValueError("Bu mesaj için kendi adınızı girin.")
    result = text.format(ad=sender.strip(), alici=recipient.strip())
    validate_message_text(result)
    return result
