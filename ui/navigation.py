from __future__ import annotations

NAV_ITEMS = ("Upload", "Study Plan", "Study Mode", "AI Tutor", "Final Exam", "Dashboard")
DEFAULT_CURRENT_PAGE = "Upload"
NAV_TRANSLATION_KEYS = {
    "Upload": "upload",
    "Study Plan": "study_plan",
    "Study Mode": "study_mode",
    "AI Tutor": "ai_tutor",
    "Final Exam": "final_exam",
    "Dashboard": "dashboard",
}


def normalize_current_page(value: str | None) -> str:
    return value if value in NAV_ITEMS else DEFAULT_CURRENT_PAGE
