from __future__ import annotations

import html

import streamlit as st

from services.progress_service import ProgressService
from translations import t
from ui.components import card
from ui.state import format_seconds, has_pdf, overall_progress
from ui.workflow import build_weak_topic_review, next_recommended_section, recommended_review_sections


def render_dashboard() -> None:
    st.subheader(t("dashboard"))
    if not has_pdf():
        st.info(t("upload_pdf_first"))
        return

    progress = st.session_state.progress
    cols = st.columns(4)
    cols[0].metric(t("learning_progress"), f"{overall_progress():.0f}%")
    cols[1].metric(t("completed_sessions"), f"{len(progress.completed_sections)}/{len(st.session_state.sections)}")
    cols[2].metric(t("quiz_average"), f"{ProgressService.quiz_average(progress):.0f}%")
    readiness = progress.final_exam_score if progress.final_exam_score is not None else overall_progress()
    cols[3].metric(t("exam_readiness"), f"{readiness:.0f}%")
    st.progress(overall_progress() / 100)

    total_sections = max(1, len(st.session_state.sections))
    average_seconds = progress.actual_study_seconds // total_sections
    with st.expander(t("study_time")):
        cols = st.columns(2)
        cols[0].metric(t("total_study_time"), format_seconds(progress.actual_study_seconds))
        cols[1].metric(t("average_per_section"), format_seconds(average_seconds))

    if not progress.completed_sections and not progress.section_quiz_scores and progress.final_exam_score is None:
        st.info(t("no_progress_yet"))

    review = progress.weak_sections or recommended_review_sections()
    next_section = next_recommended_section()
    recommendation = []
    if review:
        recommendation.append(t("review_before_exam", title=review[0]))
    if next_section:
        recommendation.append(t("recommended_next_section", title=next_section.title))
    card(t("recommendations"), html.escape(" ".join(recommendation) if recommendation else t("keep_reviewing")))

    if progress.weak_topics:
        card(t("weak_topics"), html.escape(", ".join(progress.weak_topics)))
    if progress.weak_sections:
        card(t("weak_sections"), html.escape(", ".join(progress.weak_sections)))

    if st.button(t("review_weak_topics"), type="primary"):
        st.session_state.weak_topic_review = build_weak_topic_review()
    if st.session_state.weak_topic_review:
        st.markdown(st.session_state.weak_topic_review)
