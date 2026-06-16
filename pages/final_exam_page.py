from __future__ import annotations

import html
from typing import Any

import streamlit as st

from services.exam_grading_service import ExamGradingService
from translations import current_language, t
from ui.components import card
from ui.state import has_pdf, persist_current_state
from ui.workflow import generate_final_exam


def render_final_exam() -> None:
    st.subheader(t("final_exam"))
    if not has_pdf():
        st.info(t("upload_pdf_first"))
        return

    cols = st.columns(2)
    question_count = cols[0].number_input(t("questions"), min_value=3, max_value=25, value=10)
    difficulty = cols[1].selectbox(
        t("difficulty"),
        ["mixed", "easy", "medium", "hard"],
        format_func=lambda value: t(f"difficulty_{value}"),
    )
    if st.button(t("generate_final_exam"), type="primary"):
        with st.spinner(t("generating_final_exam")):
            st.session_state.final_exam = generate_final_exam(int(question_count), difficulty)
            st.session_state.final_exam_answers = {}
            st.session_state.final_exam_result = None
            persist_current_state()
        st.success(t("final_exam_generated"))

    exam = st.session_state.final_exam
    if not exam:
        st.info(t("generate_exam_hint"))
        return

    if exam.get("fallback_used"):
        st.warning(exam.get("fallback_note", t("fallback_exam_used")))

    st.markdown(f"### {exam.get('title', t('ai_final_exam'))}")
    render_exam_form(exam)
    render_exam_result()


def render_exam_form(exam: dict[str, Any]) -> None:
    with st.form("final-exam-form"):
        answers: dict[str, Any] = {}
        for question in exam.get("questions", []):
            question_id = str(question.get("id", len(answers) + 1))
            question_type = str(question.get("type", "short_answer"))
            answer_key = f"final-exam-answer-{question_id}"
            if question_id in st.session_state.final_exam_answers:
                st.session_state.setdefault(answer_key, st.session_state.final_exam_answers[question_id])
            st.markdown(f"**{question_id}. {question.get('question', '')}**")

            if question_type in {"multiple_choice", "true_false"} and (question.get("options") or question_type == "true_false"):
                options = question.get("options") or ([t("true"), t("false")] if question_type == "true_false" else [])
                answers[question_id] = st.radio(
                    t("answer"),
                    options,
                    key=answer_key,
                    label_visibility="collapsed",
                    index=None,
                )
            else:
                answers[question_id] = st.text_area(
                    t("short_answer"),
                    key=answer_key,
                    label_visibility="collapsed",
                    height=90,
                )
            st.caption(f"{t('topic')}: {question.get('topic', t('review'))}")

        submitted = st.form_submit_button(t("submit_exam"), type="primary")

    if submitted:
        st.session_state.final_exam_answers = {key: value for key, value in answers.items() if value is not None}
        result = ExamGradingService.grade_exam(
            exam,
            st.session_state.final_exam_answers,
            st.session_state.sections,
            language=current_language(),
        )
        st.session_state.final_exam_result = result
        st.session_state.progress.final_exam_score = float(result["score"])
        st.session_state.progress.weak_topics = result["weak_topics"]
        st.session_state.progress.weak_sections = result["weak_sections"]
        persist_current_state()
        st.success(t("final_exam_submitted"))


def render_exam_result() -> None:
    result = st.session_state.final_exam_result
    if not result:
        return

    cols = st.columns(3)
    cols[0].metric(t("score"), f"{result['score']}%")
    cols[1].metric(t("correct_answers"), result["correct_count"])
    cols[2].metric(t("wrong_answers"), result["wrong_count"])

    weak_sections = result.get("weak_sections", [])
    weak_topics = result.get("weak_topics", [])
    if weak_sections:
        card(t("related_weak_sections"), html.escape(", ".join(weak_sections)))
    elif weak_topics:
        card(t("weak_topics"), html.escape(", ".join(weak_topics)))

    card(t("recommendation"), html.escape(result.get("recommendation", t("review_missed_default"))))

    missed = [item for item in result.get("results", []) if not item.get("is_correct")]
    if not missed:
        st.success(t("all_answers_correct"))
        return

    st.markdown(f"**{t('review_missed_answers')}**")

    for item in missed:
        related = f"{t('related_section')}: {item['related_section']}" if item.get("related_section") else ""

        with st.container(border=True):
            st.markdown(f"**❌ Q{item['id']}: {item.get('question', '')}**")

            st.markdown(f"**{t('your_answer')}**")
            st.write(item.get("user_answer") or t("no_answer_provided"))

            st.markdown(f"**{t('correct_answer')}**")
            st.write(item.get("expected_answer") or t("no_expected_answer"))

            if item.get("feedback"):
                st.markdown(f"**{t('feedback')}**")
                st.write(item["feedback"])

            if related:
                st.caption(related)

            if item.get("related_section"):
                if st.button(t("review_section"), key=f"review-section-{item['id']}"):
                    go_to_section(item["related_section"])


def go_to_section(section_title: str) -> None:
    for index, section in enumerate(st.session_state.sections):
        if section.title == section_title:
            st.session_state.current_section_index = index
            st.session_state.current_page = "Study Mode"
            persist_current_state()
            st.rerun()
