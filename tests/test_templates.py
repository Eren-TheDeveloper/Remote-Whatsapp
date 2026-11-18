import json
from pathlib import Path
import tempfile
import unittest

from templates import load_templates, make_template, render_message, save_templates


class TemplateTests(unittest.TestCase):
    def test_defaults_are_independent_and_do_not_write_on_load(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "messages.json"
            messages = load_templates(path)
            self.assertFalse(path.exists())
            messages[0]["text"] = "Changed"
            self.assertNotEqual(load_templates(path)[0]["text"], "Changed")

    def test_create_edit_delete_round_trip_with_unicode_and_newlines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "messages.json"
            item = make_template("Tanışma", "Merhaba {alici},\nben {ad}.")
            save_templates([item], path)
            self.assertEqual(load_templates(path), [item])
            edited = make_template("Yeni başlık", "Teşekkürler!", item["id"])
            save_templates([edited], path)
            self.assertEqual(load_templates(path), [edited])
            save_templates([], path)
            self.assertEqual(load_templates(path), [])

    def test_personalization(self):
        self.assertEqual(render_message("Merhaba {alici}, ben {ad}.", " Eren ", " Deniz "), "Merhaba Deniz, ben Eren.")
        self.assertEqual(render_message("Merhaba {alici}!", "", "Deniz"), "Merhaba Deniz!")
        self.assertEqual(render_message("{{örnek}}", "", "Deniz"), "{örnek}")

    def test_missing_fields_rejected(self):
        for text, sender, recipient in [("Merhaba", "", ""), ("Ben {ad}", "", "Deniz")]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                render_message(text, sender, recipient)

    def test_keyboard_commands_in_personalization_are_rejected(self):
        for sender, recipient in [("Name\ue007", "Deniz"), ("Eren", "Deniz\ue007")]:
            with self.subTest(sender=sender, recipient=recipient), self.assertRaises(ValueError):
                render_message("Merhaba {alici}, ben {ad}.", sender, recipient)

    def test_invalid_messages_rejected(self):
        for title, text in [("", "Hi"), ("Hello", " "), ("Test", "{unknown}"), ("Test", "{ad.__class__}"), ("Test", "{ad!r}"), ("Test", "{"), ("Test", "{ad:>20}")]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                make_template(title, text)

    def test_bad_file_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "messages.json"
            for content in ["invalid json", '{}', '[{"id": "a"}]']:
                path.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_templates(path)
                self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_duplicate_ids_cannot_replace_valid_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "messages.json"
            item = make_template("Test", "Hello")
            save_templates([item], path)
            with self.assertRaises(ValueError):
                save_templates([item, item], path)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), [item])
