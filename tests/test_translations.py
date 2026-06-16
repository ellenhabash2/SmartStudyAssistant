from __future__ import annotations

import unittest

from services.exam_service import ExamOptions, ExamService
from services.general_ai_service import GeneralAIService
from services.quiz_service import QuizService
from services.study_service import StudyService
from translations import SUPPORTED_LANGUAGES, TRANSLATIONS, translate


class TranslationTests(unittest.TestCase):
    def test_all_languages_have_same_translation_keys(self):
        expected = set(TRANSLATIONS["en"])
        self.assertEqual(set(SUPPORTED_LANGUAGES), set(TRANSLATIONS))

        for language, values in TRANSLATIONS.items():
            self.assertEqual(set(values), expected, f"Missing or extra keys for {language}")

    def test_translation_falls_back_to_key_for_unknown_key(self):
        self.assertEqual(translate("missing_key", "en"), "missing_key")
        self.assertEqual(translate("missing_key", "he"), "missing_key")

    def test_study_plan_prompt_changes_by_language(self):
        self.assertIn("English", StudyService.build_study_plan_prompt("en"))
        self.assertIn("עברית", StudyService.build_study_plan_prompt("he"))

    def test_tutor_prompt_changes_by_language(self):
        self.assertIn("English", GeneralAIService.build_tutor_prompt("en"))
        self.assertIn("ענה בעברית בלבד", GeneralAIService.build_tutor_prompt("he"))

    def test_quiz_prompt_changes_by_language(self):
        self.assertIn("English", QuizService.build_quiz_prompt("en"))
        self.assertIn("Hebrew", QuizService.build_quiz_prompt("he"))

    def test_exam_prompt_changes_by_language(self):
        english = ExamService.build_exam_prompt("Study material", ExamOptions(language="en"))
        hebrew = ExamService.build_exam_prompt("Study material", ExamOptions(language="he"))

        self.assertIn("English", english)
        self.assertIn("עברית", hebrew)


if __name__ == "__main__":
    unittest.main()
