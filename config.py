"""Portable paths and shared Chrome setup."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def validate_message_text(text):
    """Reject characters WebDriver could interpret as keyboard commands."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Mesaj metni boş olamaz.")
    if any("\ue000" <= character <= "\uf8ff" or
           (ord(character) < 32 and character not in "\n\r") or
           ord(character) == 127 for character in text):
        raise ValueError("Mesaj desteklenmeyen kontrol veya özel klavye karakterleri içeriyor.")


def configured_path(variable, default):
    value = Path(os.environ.get(variable) or default).expanduser()
    return value if value.is_absolute() else BASE_DIR / value


def data_path():
    return configured_path("WHATSAPP_DATA_FILE", "whatsapp_data.json")


def create_driver():
    from selenium import webdriver

    options = webdriver.ChromeOptions()
    profile = configured_path("WHATSAPP_CHROME_USER_DATA_DIR", ".chrome-profile")
    options.add_argument(f"--user-data-dir={profile}")
    profile_name = os.environ.get("WHATSAPP_CHROME_PROFILE")
    if profile_name:
        options.add_argument(f"--profile-directory={profile_name}")
    return webdriver.Chrome(options=options)


def xpath_literal(value):
    """Quote a value safely inside an XPath expression."""
    if '"' not in value:
        return f'"{value}"'
    if "'" not in value:
        return f"'{value}'"
    parts = [f'"{part}"' for part in value.split('"')]
    quote = "'" + '"' + "'"
    return "concat(" + (", " + quote + ", ").join(parts) + ")"
