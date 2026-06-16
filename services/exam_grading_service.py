from __future__ import annotations

import re
from typing import Any

from services.study_service import StudySection
from services.ai_answer_grading_service import AIAnswerGradingService
from translations import normalize_language, translate


class ExamGradingService:
    """Grade generated final exams and map misses back to study sections."""

    @classmethod
    def grade_exam(
        cls,
        exam: dict[str, Any],
        answers: dict[str, Any],
        sections: list[StudySection],
        language: str = "en",
    ) -> dict[str, Any]:
        language = normalize_language(language)
        questions = [item for item in exam.get("questions", []) if isinstance(item, dict)]
        results: list[dict[str, Any]] = []
        weak_topics: list[str] = []
        weak_sections: list[str] = []
        correct_count = 0

        for question in questions:
            question_id = str(question.get("id", len(results) + 1))
            user_answer = str(answers.get(question_id, "") or "").strip()
            expected = str(question.get("answer", "") or "").strip()
            question_type = str(question.get("type", "short_answer"))
            is_correct = cls._is_correct(question, question_type, user_answer, expected, language)
            related_section = cls.related_section(question, sections)

            if is_correct:
                correct_count += 1
            else:
                topic = str(question.get("topic", "") or translate("review", language)).strip()
                if topic and topic not in weak_topics:
                    weak_topics.append(topic)
                if related_section and related_section.title not in weak_sections:
                    weak_sections.append(related_section.title)

            results.append(
                {
                    "id": question.get("id"),
                    "question": question.get("question", ""),
                    "type": question_type,
                    "user_answer": user_answer,
                    "expected_answer": expected,
                    "is_correct": is_correct,
                    "topic": question.get("topic", translate("review", language)),
                    "related_section": related_section.title if related_section else "",
                }
            )

        total = max(1, len(questions))
        score = round(correct_count / total * 100)
        return {
            "score": score,
            "correct_count": correct_count,
            "wrong_count": len(questions) - correct_count,
            "total": len(questions),
            "weak_topics": weak_topics,
            "weak_sections": weak_sections,
            "results": results,
            "recommendation": cls.recommendation(weak_sections, weak_topics, language),
        }

    @staticmethod
    def recommendation(weak_sections: list[str], weak_topics: list[str], language: str = "en") -> str:
        language = normalize_language(language)
        if weak_sections:
            if language == "he":
                return f"חזרו קודם על {weak_sections[0]}, ואז נסו שוב את השאלות שפספסתם."
            return f"Review {weak_sections[0]} first, then retry the missed questions."
        if weak_topics:
            if language == "he":
                return f"חזרו על {weak_topics[0]} וכתבו סיכום במשפט אחד לפני ניסיון נוסף במבחן."
            return f"Review {weak_topics[0]} and write a one-sentence summary before retaking the exam."
        if language == "he":
            return "עבודה טובה. עברו בקצרה על ההערות לפני שממשיכים."
        return "Good work. Revisit your notes briefly before moving on."

    @classmethod
    def related_section(cls, question: dict[str, Any], sections: list[StudySection]) -> StudySection | None:
        haystack = " ".join(
            str(question.get(key, "") or "")
            for key in ("question", "answer", "topic")
        )
        question_tokens = cls._tokens(haystack)
        if not question_tokens:
            return None

        best_section: StudySection | None = None
        best_score = 0
        for section in sections:
            section_text = " ".join(
                [
                    section.title,
                    section.summary,
                    " ".join(section.key_concepts),
                    " ".join(section.learning_objectives),
                ]
            )
            score = len(question_tokens & cls._tokens(section_text))
            if score > best_score:
                best_score = score
                best_section = section
        return best_section if best_score > 0 else None

    @classmethod
    def _is_correct(
            cls,
            question: dict[str, Any],
            question_type: str,
            user_answer: str,
            expected: str,
            language: str = "en",
    ) -> bool:
        if not user_answer:
            return False

        if question_type in {"multiple_choice", "true_false"}:
            normalized_user = cls._normalize(user_answer)
            normalized_expected = cls._normalize(expected)

            if normalized_user == normalized_expected:
                return True

            user_letter = cls._extract_option_letter(user_answer)
            expected_letter = cls._extract_option_letter(expected)

            if user_letter and expected_letter:
                return user_letter == expected_letter

            options = question.get("options", [])
            if expected_letter and isinstance(options, list):
                option_index = ord(expected_letter) - ord("a")
                if 0 <= option_index < len(options):
                    expected_option = cls._normalize(str(options[option_index]))
                    return normalized_user == expected_option

            return False

        normalized_user = cls._normalize(user_answer)
        normalized_expected = cls._normalize(expected)
        if normalized_user and (
            normalized_user == normalized_expected
            or normalized_user in normalized_expected
            or normalized_expected in normalized_user
        ):
            return True

        evaluation = AIAnswerGradingService.grade_short_answer(
            question=str(question.get("question", "")),
            expected_answer=expected,
            user_answer=user_answer,
            language=language,
        )
        return int(evaluation.get("score", 0)) >= 70

    @staticmethod
    def _normalize(value: str) -> str:
        value = re.sub(r"^\s*[A-Da-d][.)]\s*", "", value or "")
        return re.sub(r"\s+", " ", value).strip().lower()

    @staticmethod
    def _extract_option_letter(value: str) -> str:
        match = re.match(r"^\s*([A-Da-d])(?:[.)]|\s*$)", value or "")
        return match.group(1).lower() if match else ""

    @staticmethod
    def _tokens(value: str) -> set[str]:
        stop_words = {
            "about", "answer", "based", "explain", "from", "idea", "important",
            "material", "question", "review", "section", "study", "this", "with",
        }
        return {
            token
            for token in re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", (value or "").lower())
            if token not in stop_words
        }
