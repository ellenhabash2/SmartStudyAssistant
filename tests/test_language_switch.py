from __future__ import annotations

import unittest

from translations import current_language, rtl_css, set_language, translate


class LanguageSwitchTests(unittest.TestCase):
    def tearDown(self):
        set_language("en")

    def test_language_switch_updates_current_language(self):
        set_language("he")
        self.assertEqual(current_language(), "he")
        self.assertEqual(translate("dashboard"), "לוח בקרה")

        set_language("en")
        self.assertEqual(current_language(), "en")
        self.assertEqual(translate("dashboard"), "Dashboard")

    def test_rtl_css_applies_for_hebrew(self):
        css = rtl_css("he")
        self.assertIn("direction: rtl", css)
        self.assertIn("text-align: right", css)

    def test_ltr_css_applies_for_english(self):
        css = rtl_css("en")
        self.assertIn("direction: ltr", css)
        self.assertIn("text-align: left", css)


if __name__ == "__main__":
    unittest.main()
