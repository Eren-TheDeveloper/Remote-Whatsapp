"""Send a WhatsApp message or transcribe a short Turkish voice recording."""
import argparse
import json

from config import create_driver, data_path, validate_message_text, xpath_literal


def load_data():
    with data_path().open(encoding="utf-8") as handle:
        return json.load(handle)


def Listener():
    import sounddevice as sd
    import speech_recognition as sr

    sample_rate = 44100
    print("Dinleniyor...")
    audio = sd.rec(5 * sample_rate, samplerate=sample_rate, channels=1, dtype="int16")
    sd.wait()
    recognizer = sr.Recognizer()
    audio_data = sr.AudioData(audio.tobytes(), sample_rate, 2)
    try:
        return recognizer.recognize_google(audio_data, language="tr-TR").lower()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as error:
        raise RuntimeError("Ses tanıma hizmetine ulaşılamadı.") from error


def send_message(name, text):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    if not name.strip() or not text.strip():
        raise ValueError("Alıcı ve mesaj boş olamaz.")
    validate_message_text(text)
    driver = create_driver()
    try:
        driver.maximize_window()
        driver.get("https://web.whatsapp.com/")
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.ID, "pane-side"))
        )
        contacts = WebDriverWait(driver, 15).until(
            EC.visibility_of_any_elements_located(
                (By.XPATH, f'//*[@id="pane-side"]//span[@title={xpath_literal(name)}]')
            )
        )
        if len(contacts) != 1:
            raise RuntimeError("Aynı adla birden fazla sohbet var. WhatsApp'ta alıcıya benzersiz bir ad verin.")
        contacts[0].click()
        message_box = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '#main footer [contenteditable="true"][role="textbox"]')
            )
        )
        if (message_box.get_attribute("textContent") or "").strip():
            raise RuntimeError("Bu sohbette taslak mesaj var. WhatsApp'ta taslağı temizleyip tekrar deneyin.")
        # Enter sends in WhatsApp; Shift+Enter inserts a line break.
        for index, line in enumerate(text.replace("\r\n", "\n").replace("\r", "\n").split("\n")):
            if index:
                message_box.send_keys(Keys.SHIFT, Keys.ENTER, Keys.NULL)
            if line:
                message_box.send_keys(line)
        message_box.send_keys(Keys.RETURN)
        WebDriverWait(driver, 15).until(
            lambda _: not (message_box.get_attribute("textContent") or "").strip()
        )
        print(f"Mesaj gönderme komutu uygulandı: {name}")
    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("gui", help="Hazır mesaj penceresini açar")
    send = commands.add_parser("send", help="Belirtilen sohbete mesaj gönderir")
    send.add_argument("name", help="Görünür sohbet listesindeki tam ad")
    send.add_argument("text", help="Gönderilecek mesaj")
    commands.add_parser("listen", help="5 saniyelik Türkçe sesi yazıya çevirir")
    args = parser.parse_args()
    if args.command in (None, "gui"):
        from gui import launch
        launch()
    elif args.command == "send":
        send_message(args.name, args.text)
    else:
        print(Listener())


if __name__ == "__main__":
    main()
