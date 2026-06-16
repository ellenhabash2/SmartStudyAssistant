from __future__ import annotations

from typing import Any, Callable

from translations import normalize_language


ShortAnswerEvaluator = Callable[[dict[str, Any], Any], dict[str, Any]]


class QuizGradingService:
    """Grade section quizzes while allowing UI code to supply short-answer evaluation."""

    @staticmethod
    def grade(
        questions: list[dict[str, Any]],
        answers: dict[int, Any],
        short_answer_evaluator: ShortAnswerEvaluator | None = None,
        language: str = "en",
    ) -> tuple[int, list[str]]:
        language = normalize_language(language)
        correct = 0.0
        feedback: list[str] = []

        for index, question in enumerate(questions, start=1):
            user_answer = answers.get(index)

            if question["type"] in {"multiple_choice", "true_false"}:
                if user_answer == question["answer"]:
                    correct += 1
                    feedback.append(f"Q{index}: {'נכון.' if language == 'he' else 'Correct.'}")
                else:
                    if language == "he":
                        feedback.append(f"Q{index}: לא נכון. התשובה הנכונה היא: {question['answer']}")
                    else:
                        feedback.append(f"Q{index}: Incorrect. The correct answer was: {question['answer']}")
                continue

            if short_answer_evaluator is None:
                evaluation = {"score": 0, "feedback": "לא ניתן לבדוק." if language == "he" else "Could not grade."}
            else:
                evaluation = short_answer_evaluator(question, user_answer)
            correct += float(evaluation.get("score", 0)) / 100
            feedback.append(f"Q{index}: {evaluation.get('feedback', 'לא ניתן לבדוק.' if language == 'he' else 'Could not grade.')}")

        score = round((correct / max(1, len(questions))) * 100)
        return score, feedback
