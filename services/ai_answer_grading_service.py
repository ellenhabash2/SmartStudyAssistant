from __future__ import annotations

import re
from typing import Any

from services.general_ai_service import GeneralAIService
from translations import normalize_language


class AIAnswerGradingService:
    """Shared AI-based grading for short-answer questions."""

    @staticmethod
    def grade_short_answer(
        question: str,
        expected_answer: str,
        user_answer: Any,
        context: str = "",
        language: str = "en",
    ) -> dict[str, Any]:
        language = normalize_language(language)
        if not str(user_answer or "").strip():
            return {"score": 0, "feedback": "לא ניתנה תשובה." if language == "he" else "No answer was provided."}

        language_instruction = (
            "Write the score and feedback in Hebrew."
            if language == "he"
            else "Write the score and feedback in English."
        )
        prompt = (
            f"Study context: {context}\n\n"
            f"Question: {question}\n"
            f"Expected answer: {expected_answer}\n"
            f"User's answer: {user_answer}\n\n"
            f"{language_instruction}\n"
            "Evaluate the answer strictly based on the provided context and expected answer. "
            "Use semantic meaning, not exact wording. "
            "Provide a score from 0 to 100 and short feedback. "
            "Format: Score: [0-100] | Feedback: [Explanation]"
        )

        response = GeneralAIService().ask([], prompt, language=language)
        if not response["ok"]:
            return {"score": 0, "feedback": "לא ניתן לבדוק את התשובה." if language == "he" else "Could not grade."}

        score_match = re.search(r"Score:\s*(\d+)", response["answer"])
        score = int(score_match.group(1)) if score_match else 0

        return {
            "score": max(0, min(score, 100)),
            "feedback": response["answer"],
        }
