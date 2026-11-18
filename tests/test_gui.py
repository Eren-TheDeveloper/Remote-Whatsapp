import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from gui import QuickMessages


class QuickMessageWindowTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"Display unavailable: {error}")
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        with patch("gui.load_templates", return_value=[{
            "id": "intro", "title": "Hello", "text": "Merhaba {alici}, ben {ad}."
        }]):
            self.app = QuickMessages(self.root)

    def test_previews_update_with_personalization(self):
        self.app.recipient.set("Deniz")
        self.app.sender.set("Eren")
        self.assertEqual(self.app.cards[0][1].cget("text"), "Merhaba Deniz, ben Eren.")

    def test_click_sends_snapshot_and_blocks_duplicate_clicks(self):
        self.app.recipient.set("Deniz")
        self.app.sender.set("Eren")
        with patch("gui.threading.Thread") as thread:
            self.app.send(self.app.templates[0])
            self.app.send(self.app.templates[0])
            thread.assert_called_once()
            self.assertTrue(self.app.busy)
            self.assertTrue(all(str(button.cget("state")) == "disabled" for button in self.app.action_buttons))
            self.app.recipient.set("Changed")
            with patch("main.send_message") as send:
                thread.call_args.kwargs["target"]()
                send.assert_called_once_with("Deniz", "Merhaba Deniz, ben Eren.")
        self.app.poll()
        self.assertFalse(self.app.busy)

    def test_failed_send_restores_buttons_and_shows_error(self):
        self.app.recipient.set("Deniz")
        self.app.sender.set("Eren")
        with patch("gui.threading.Thread") as thread, patch("main.send_message", side_effect=RuntimeError("Offline")):
            self.app.send(self.app.templates[0])
            thread.call_args.kwargs["target"]()
        with patch("gui.messagebox.showerror") as error:
            self.app.poll()
            error.assert_called_once()
        self.assertFalse(self.app.busy)

    def test_failed_save_keeps_current_collection(self):
        original = list(self.app.templates)
        with patch("gui.save_templates", side_effect=OSError("Disk full")), patch("gui.messagebox.showerror"):
            self.assertFalse(self.app.persist([]))
        self.assertEqual(self.app.templates, original)

    def test_missing_recipient_does_not_send(self):
        with patch("gui.threading.Thread") as thread, patch("gui.messagebox.showerror"):
            self.app.send(self.app.templates[0])
            thread.assert_not_called()
