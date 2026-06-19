from __future__ import annotations

import html
import random
import re
import tempfile
from pathlib import Path
from typing import Any

import streamlit as st

from services.exam_service import ExamOptions, ExamService
from services.general_ai_service import GeneralAIService
from services.pdf_service import PdfExtractionError, PdfService
from services.progress_service import ProgressService
from services.quiz_service import QuizService
from services.section_state_service import SectionStateService
from services.study_service import StudySection, StudyService
from translations import current_language, t, tutor_language_instruction
from ui.state import has_pdf, page_label, persist_current_state, reset_section_outputs, section_context, source_label


def extract_pdf(uploaded_file: Any) -> None:
    pdf_bytes = uploaded_file.getvalue()
    tmp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp_path = Path(tmp_file.name)

    try:
        tmp_file.write(pdf_bytes)
        tmp_file.close()
        pages = PdfService().extract_pages(str(tmp_path))
        set_pending_pdf(pdf_bytes, uploaded_file.name, pages)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


def set_pending_pdf(pdf_bytes: bytes, pdf_name: str, pages: list[Any]) -> None:
    st.session_state.pending_pdf_bytes = pdf_bytes
    st.session_state.pending_pdf_name = pdf_name
    st.session_state.pending_pages = pages
    suggested = StudyService.suggest_session_count(pages)
    st.session_state.suggested_session_count = suggested
    st.session_state.selected_session_count = suggested
    st.session_state.pending_sections = StudyService().generate_study_plan_for_sessions(
        pages,
        suggested,
        language=current_language(),
    )

    if not st.session_state.pending_sections:
        raise PdfExtractionError(t("no_readable_sessions"))

    st.session_state.upload_message = t("processed_pdf_ready", pdf_name=pdf_name)


def generate_study_plan_from_pending() -> None:
    pages = st.session_state.pending_pages
    session_count = int(st.session_state.selected_session_count or st.session_state.suggested_session_count or 1)
    sections = StudyService().generate_study_plan_for_sessions(
        pages,
        session_count,
        language=current_language(),
    )
    if not sections:
        raise PdfExtractionError(t("no_readable_sessions"))

    st.session_state.pdf_bytes = st.session_state.pending_pdf_bytes
    st.session_state.pdf_name = st.session_state.pending_pdf_name
    st.session_state.pages = pages
    st.session_state.sections = sections
    st.session_state.section_states = SectionStateService.ensure_states(
        {},
        [section.section_number for section in sections],
    )
    st.session_state.current_section_index = 0
    st.session_state.upload_message = t("generated_sessions", count=len(sections))
    st.session_state.progress = ProgressService.default_state()
    st.session_state.final_exam = None
    st.session_state.final_exam_answers = {}
    st.session_state.final_exam_result = None
    reset_section_outputs(sections[0])
    persist_current_state()


def generate_explanation(section: StudySection) -> str:
    text = section_context(section)
    language = current_language()
    concepts = ", ".join(section.key_concepts[:4]) or ("הרעיונות המרכזיים" if language == "he" else "the main ideas")

    prompt = (
        "Explain this study section for a student preparing for an exam.\n"
        f"{tutor_language_instruction(language)}\n"
        "Use the provided section text only.\n"
        "Structure the answer with these headings:\n"
        "Summary, Key Ideas, Important Definitions, Exam Tips.\n"
        "Keep it clear and practical.\n\n"
        f"Section title: {section.title}\n"
        f"Pages: {section.page_label}\n"
        f"Key concepts: {concepts}\n\n"
        f"Section text:\n{text[:6000]}"
    )

    response = GeneralAIService().ask([], prompt, language=language)
    if response["ok"]:
        provider = response.get("provider", "AI")
        return f"{response['answer']}\n\n_AI provider: {provider}_\n\n{source_label(section)}"

    sentences = [item.strip() for item in text.replace("\n", " ").split(".") if len(item.split()) >= 6]
    summary = " ".join(sentence + "." for sentence in sentences[:2]) or section.summary
    definitions = section.key_concepts[:3] or [t("fallback_core_idea"), t("fallback_example"), t("fallback_review_point")]

    if language == "he":
        return (
            f"**סיכום**\n\n{summary}\n\n"
            f"**רעיונות מרכזיים**\n\n- {concepts}\n- קשרו את הדוגמאות ב{page_label(section)} לכותרת החלק.\n\n"
            f"**הגדרות חשובות**\n\n"
            + "\n".join(f"- {term}: הגדירו את המונח מתוך הערות החלק." for term in definitions)
            + "\n\n**טיפים למבחן**\n\n"
            "- ודאו שאתם יכולים להסביר את החלק במילים שלכם.\n"
            "- תרגלו דוגמה אחת בלי להסתכל ב-PDF.\n"
            "- חזרו על כל מושג מרכזי שאינכם יכולים להגדיר במהירות.\n\n"
            f"_הסבר גיבוי לא מקוון_\n\n{source_label(section)}"
        )

    return (
        f"**Summary**\n\n{summary}\n\n"
        f"**Key Ideas**\n\n- {concepts}\n- Connect the examples on {section.page_label.lower()} to the section title.\n\n"
        f"**Important Definitions**\n\n"
        + "\n".join(f"- {term}: define this term from the section notes." for term in definitions)
        + "\n\n**Exam Tips**\n\n"
        "- Be ready to explain the section in your own words.\n"
        "- Practice one example without looking at the PDF.\n"
        "- Review any key concept tag you cannot define quickly.\n\n"
        f"_Offline fallback explanation_\n\n{source_label(section)}"
    )

def relevant_document_context(question: str, current_section: StudySection, max_chars: int = 12000) -> tuple[str, list[int]]:
    stop_words = {
        "what", "are", "the", "for", "and", "that", "this", "with", "from",
        "does", "have", "into", "about", "which", "when", "where", "why",
        "how", "is", "a", "an", "of", "to", "in", "on",
    }

    question_terms = {
        token
        for token in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", question.lower())
        if token not in stop_words
    }

    ranked_pages: list[tuple[int, int, str]] = []

    for page in st.session_state.pages:
        page_text = (getattr(page, "text", "") or "").strip()
        if not page_text:
            continue

        page_number = int(getattr(page, "page_number", 0) or 0)
        page_tokens = set(re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", page_text.lower()))
        score = len(question_terms & page_tokens)

        if current_section.start_page <= page_number <= current_section.end_page:
            score += 1

        if score > 0:
            ranked_pages.append((score, page_number, page_text))

    ranked_pages.sort(key=lambda item: (-item[0], item[1]))

    parts: list[str] = []
    source_pages: list[int] = []

    for _, page_number, page_text in ranked_pages[:8]:
        parts.append(f"[Page {page_number}]\n{page_text}")
        source_pages.append(page_number)

        if sum(len(part) for part in parts) >= max_chars:
            break

    if not parts:
        return "", ""

    return "\n\n".join(parts)[:max_chars], source_pages

def question_language(question: str, default_language: str) -> str:
    if re.search(r"[\u0590-\u05FF]", question or ""):
        return "he"

    return default_language

def answer_section_question(section: StudySection, question: str) -> str:
    language = question_language(question, current_language())
    section_text = section_context(section)
    document_context, source_pages = relevant_document_context(question, section)

    if language == "he":
        fallback_message = "המסמך שהועלה אינו מכיל מספיק מידע כדי לענות על השאלה."
    else:
        fallback_message = "The uploaded PDF does not contain enough information to answer this question."

    if not document_context.strip():
        return fallback_message

    prompt = (
        "Answer the student's question using ONLY the uploaded PDF content below.\n"
        "You may use the current section and other relevant pages from the same PDF.\n"
        "Do not use outside knowledge.\n"
        "If the answer is not clearly supported by the PDF content, respond exactly with:\n"
        f"\"{fallback_message}\"\n\n"
        f"{tutor_language_instruction(language)}\n\n"
        f"Current section title: {section.title}\n"
        f"Current section pages: {section.page_label}\n\n"
        f"Current section text:\n{section_text[:3000]}\n\n"
        f"Relevant uploaded PDF content:\n{document_context}\n\n"
        f"Question:\n{question}"
    )

    response = GeneralAIService().ask([], prompt, language=language)

    if response["ok"]:
        answer = response["answer"].strip()

        if answer == fallback_message:
            return answer

        if source_pages:
            source = f"Source: Pages {min(source_pages)}-{max(source_pages)}"
        else:
            source = source_label(section)

        found_in_current_section = any(
            section.start_page <= page <= section.end_page
            for page in source_pages
        )

        if source_pages and not found_in_current_section:
            return f"{answer}\n\n{source}\nNote: This answer was found outside the current study section."

        return f"{answer}\n\n{source}"

    return fallback_message


def answer_ai_tutor(question: str, use_pdf_context: bool = False) -> dict[str, Any]:
    language = current_language()
    context_message = ""
    if use_pdf_context and has_pdf():
        context_message = all_study_context()[:6000]

    messages = list(st.session_state.ai_tutor_history)
    if context_message:
        messages.append({"role": "user", "content": f"{tutor_language_instruction(language)}\nOptional uploaded PDF context:\n{context_message}"})

    result = GeneralAIService().ask(messages, question, language=language)
    if result["ok"]:
        return result

    if language == "he":
        available = "אפשר להשתמש בחלקים מה-PDF שהעלית." if has_pdf() else "העלו PDF כדי לתת לי הקשר לימודי."
        fallback = (
            "מורה ה-AI צריך `OPENAI_API_KEY` או `GROQ_API_KEY` כדי לענות תשובה מלאה. "
            f"{available} בינתיים נסו לשאול שאלה ממוקדת כמו "
            "\"סכם את החלק הזה\", \"בחן אותי על המושגים המרכזיים\", או "
            "\"הסבר את המונח הקשה ביותר בפשטות.\""
        )
    else:
        available = "I can use your uploaded PDF sections." if has_pdf() else "Upload a PDF to give me study context."
        fallback = (
            "AI Tutor needs `OPENAI_API_KEY` or `GROQ_API_KEY` for a full answer. "
            f"{available} For now, try asking one focused question such as "
            "\"summarize this section\", \"quiz me on the key concepts\", or "
            "\"explain the hardest term in simple words.\""
        )
    return {"ok": False, "answer": fallback, "provider": "none"}


def build_section_quiz(section: StudySection) -> list[dict[str, Any]]:
    generated = QuizService.generate_from_documents(
        [{"text": section_context(section), "source": st.session_state.pdf_name, "page": section.start_page}],
        num_questions=3,
        language=current_language(),
    )
    questions: list[dict[str, Any]] = []
    if generated:
        first = generated[0]
        options = list(first.options)
        random.shuffle(options)
        questions.append(
            {
                "type": "multiple_choice",
                "question": first.prompt,
                "options": options,
                "answer": first.answer,
                "source_page": first.page or section.start_page,
            }
        )

    concept = section.key_concepts[0] if section.key_concepts else section.title
    questions.append(
        {
            "type": "true_false",
            "question": (
                f"נכון או לא נכון: {concept} מופיע בחלק הזה."
                if current_language() == "he"
                else f"True or False: {concept} is discussed in this section."
            ),
            "options": [t("true"), t("false")],
            "answer": t("true"),
            "source_page": section.start_page,
        }
    )
    questions.append(
        {
            "type": "short_answer",
            "question": (
                f"במשפט אחד, הסבירו למה {concept} חשוב בחלק הזה."
                if current_language() == "he"
                else f"In one sentence, explain why {concept} matters in this section."
            ),
            "options": [],
            "answer": (
                "תשובה טובה צריכה להשתמש בטקסט החלק ולהזכיר בבירור את הרעיון המרכזי."
                if current_language() == "he"
                else "A strong answer should use the section text and mention the main idea clearly."
            ),
            "source_page": section.start_page,
        }
    )
    return questions


def all_study_context() -> str:
    lines: list[str] = []
    for section in st.session_state.sections:
        lines.append(f"{section.title}\n{section_context(section)}")
    return "\n\n".join(lines)


def generate_final_exam(question_count: int, difficulty: str) -> dict[str, Any]:
    return ExamService().generate_final_exam(
        all_study_context(),
        ExamOptions(question_count=int(question_count), difficulty=difficulty, language=current_language()),
    )


def recommended_review_sections() -> list[str]:
    if not has_pdf():
        return []
    progress = st.session_state.progress
    return [
        section.title
        for section in st.session_state.sections
        if section.section_number not in progress.completed_sections
    ][:3]


def next_recommended_section() -> StudySection | None:
    if not has_pdf():
        return None
    for section in st.session_state.sections:
        if section.section_number not in st.session_state.progress.completed_sections:
            return section
    return None


def build_weak_topic_review() -> str:
    review_sections = recommended_review_sections()
    if not review_sections:
        return t("weak_review_complete")

    quiz_average = ProgressService.quiz_average(st.session_state.progress)
    plans = [f"### {t('weak_review_title')}"]
    for title in review_sections:
        section = next((item for item in st.session_state.sections if item.title == title), None)
        if section is None:
            continue
        topic = section.key_concepts[0] if section.key_concepts else section.title
        reason = t("reason_low_quiz") if quiz_average and quiz_average < 80 else t("reason_not_completed")
        plans.append(
            "- **"
            + t(
                "weak_review_item",
                topic=html.escape(topic),
                reason=reason,
                number=section.section_number,
                page_label=page_label(section).lower(),
            )
            + "**"
        )
    return "\n".join(plans)
