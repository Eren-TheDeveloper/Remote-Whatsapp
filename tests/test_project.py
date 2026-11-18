import importlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import config
import main


class ProjectTests(unittest.TestCase):
    def test_default_paths_do_not_depend_on_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = Path.cwd()
            try:
                os.chdir(directory)
                with patch.dict(os.environ, {}, clear=True):
                    self.assertEqual(config.data_path(), config.BASE_DIR / "whatsapp_data.json")
            finally:
                os.chdir(previous)

    def test_environment_path_override(self):
        with patch.dict(os.environ, {"WHATSAPP_DATA_FILE": "private/data.json"}):
            self.assertEqual(config.data_path(), config.BASE_DIR / "private/data.json")

    def test_import_does_not_start_browser(self):
        with patch("config.create_driver") as create:
            import get_data
            importlib.reload(get_data)
            create.assert_not_called()

    def test_data_collection_closes_browser_on_failure(self):
        import get_data
        driver = Mock()
        driver.get.side_effect = RuntimeError("Offline")
        with patch.object(get_data, "create_driver", return_value=driver):
            with self.assertRaisesRegex(RuntimeError, "Offline"):
                get_data.get_data()
        driver.quit.assert_called_once()

    def test_sending_closes_browser_on_failure(self):
        driver = Mock()
        driver.get.side_effect = RuntimeError("Offline")
        with patch.object(main, "create_driver", return_value=driver):
            with self.assertRaisesRegex(RuntimeError, "Offline"):
                main.send_message("Example", "Hello")
        driver.quit.assert_called_once()

    def test_empty_message_does_not_start_browser(self):
        with patch.object(main, "create_driver") as create:
            with self.assertRaises(ValueError):
                main.send_message("Example", "  ")
            create.assert_not_called()

    def test_multiline_message_uses_shift_enter_and_sends_once(self):
        from selenium.webdriver.common.keys import Keys
        driver, contact, box = Mock(), Mock(), Mock()
        box.get_attribute.return_value = ""
        wait = Mock()
        wait.until.side_effect = [Mock(), [contact], box, True]
        with patch.object(main, "create_driver", return_value=driver), patch(
            "selenium.webdriver.support.ui.WebDriverWait", return_value=wait
        ):
            main.send_message("Example", "First\nSecond")
        self.assertEqual(box.send_keys.call_args_list, [
            unittest.mock.call("First"),
            unittest.mock.call(Keys.SHIFT, Keys.ENTER, Keys.NULL),
            unittest.mock.call("Second"),
            unittest.mock.call(Keys.RETURN),
        ])
        driver.quit.assert_called_once()

    def test_existing_draft_is_not_sent(self):
        driver, box = Mock(), Mock()
        box.get_attribute.return_value = "Existing draft"
        wait = Mock()
        wait.until.side_effect = [Mock(), [Mock()], box]
        with patch.object(main, "create_driver", return_value=driver), patch(
            "selenium.webdriver.support.ui.WebDriverWait", return_value=wait
        ):
            with self.assertRaisesRegex(RuntimeError, "taslak"):
                main.send_message("Example", "Hello")
        box.send_keys.assert_not_called()
        driver.quit.assert_called_once()

    def test_duplicate_recipient_is_not_clicked_or_sent(self):
        driver = Mock()
        contacts = [Mock(), Mock()]
        wait = Mock()
        wait.until.side_effect = [Mock(), contacts]
        with patch.object(main, "create_driver", return_value=driver), patch(
            "selenium.webdriver.support.ui.WebDriverWait", return_value=wait
        ):
            with self.assertRaisesRegex(RuntimeError, "birden fazla"):
                main.send_message("Example", "Hello")
        for contact in contacts:
            contact.click.assert_not_called()
        driver.quit.assert_called_once()

    def test_keyboard_commands_in_message_do_not_open_browser(self):
        for text in ["Hello\ue007Injected", "Hello\ue009a", "Hello\tInjected", "Hello\x00"]:
            with self.subTest(text=repr(text)), patch.object(main, "create_driver") as create:
                with self.assertRaises(ValueError):
                    main.send_message("Example", text)
                create.assert_not_called()

    def test_xpath_quotes(self):
        self.assertEqual(config.xpath_literal("Example"), '"Example"')
        self.assertEqual(config.xpath_literal('A "B"'), "'A \"B\"'")
        self.assertEqual(config.xpath_literal('A\'s "B"'), '''concat("A's ", '"', "B", '"', "")''')


if __name__ == "__main__":
    unittest.main()
