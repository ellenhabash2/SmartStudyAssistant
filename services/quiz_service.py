from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, List, Optional

from core.models import DocumentChunk


@dataclass(frozen=True)
class QuizQuestion:
    prompt: str
    options: List[str]
    answer: str
    explanation: Optional[str] = None
    citation: Optional[str] = None
    source: Optional[str] = None
    page: Optional[int] = None


class QuizService:
    """Simple quiz generator for document-based multiple-choice questions."""

    STOP_WORDS = {
        "the", "and", "with", "that", "this", "those", "their", "about",
        "which", "there", "where", "while", "because", "through", "between",
    }

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        text = re.sub(r"\s+", " ", text or "").strip()
        if not text:
            return []
        return [sentence.strip() for sentence in re.split(r'(?<=[.?!])\s+', text) if sentence.strip()]

    @staticmethod
    def _select_keyword(sentence: str) -> Optional[str]:
        words = [w.strip(".,;:()[]\"'`)" ) for w in sentence.split()]
        candidates = [w for w in words if len(w) > 5 and w.lower() not in QuizService.STOP_WORDS]
        return max(candidates, key=len) if candidates else None

    @staticmethod
    def _build_options(correct: str, pool: List[str], num_options: int = 4) -> List[str]:
        options = [correct]
        seen = {correct.lower()}
        for candidate in pool:
            normalized = candidate.lower()
            if normalized in seen or len(candidate) <= 3:
                continue
            seen.add(normalized)
            options.append(candidate)
            if len(options) >= num_options:
                break
        fallback_terms = ["analysis", "document", "concept", "process", "method", "record"]
        for fallback in fallback_terms:
            if len(options) >= num_options:
                break
            if fallback.lower() in seen:
                continue
            seen.add(fallback.lower())
            options.append(fallback)
        return options

    @staticmethod
    def _extract_doc_data(item: Any) -> dict[str, Any]:
        if isinstance(item, DocumentChunk):
            return {
                "text": item.text,
                "source": "Uploaded PDF",
                "page": item.page_number,
            }

        if isinstance(item, dict):
            return {
                "text": item.get("text", ""),
                "source": item.get("source", "Uploaded PDF"),
                "page": item.get("page"),
            }

        metadata = dict(getattr(item, "metadata", {}) or {})
        return {
            "text": getattr(item, "page_content", ""),
            "source": metadata.get("source", "Uploaded PDF"),
            "page": metadata.get("page"),
        }

    @classmethod
    def generate_mcq(cls, chunks: List[DocumentChunk], num_questions: int = 3) -> List[QuizQuestion]:
        """Generate simple multiple-choice questions from legacy chunk objects."""
        return cls.generate_from_documents(chunks, num_questions=num_questions)

    @classmethod
    def generate_from_documents(cls, documents: List[Any], num_questions: int = 3) -> List[QuizQuestion]:
        """Generate deterministic fill-in-the-blank questions with citations."""
        sentence_rows: List[dict[str, Any]] = []
        for item in documents:
            doc_data = cls._extract_doc_data(item)
            for sentence in cls._split_sentences(doc_data["text"]):
                if len(sentence.split()) < 8:
                    continue
                sentence_rows.append(
                    {
                        "sentence": sentence,
                        "source": doc_data["source"],
                        "page": doc_data["page"],
                    }
                )

        if not sentence_rows:
            return []

        keyword_pool: List[str] = []
        for row in sentence_rows:
            keyword = cls._select_keyword(row["sentence"])
            if keyword:
                keyword_pool.append(keyword)

        questions: List[QuizQuestion] = []
        seen_prompts = set()
        for row in sentence_rows:
            sentence = row["sentence"]
            keyword = cls._select_keyword(sentence)
            if not keyword:
                continue

            prompt = f"Fill in the blank: {sentence.replace(keyword, '_____', 1)}"
            if prompt in seen_prompts:
                continue

            options = cls._build_options(keyword, keyword_pool, num_options=4)
            if len(options) < 2:
                continue

            page = row["page"]
            source = row["source"] or "Uploaded PDF"
            citation = f"{source} p.{page}" if page else source

            questions.append(
                QuizQuestion(
                    prompt=prompt,
                    options=options,
                    answer=keyword,
                    explanation=f"The correct answer is '{keyword}'.",
                    citation=citation,
                    source=source,
                    page=page,
                )
            )
            seen_prompts.add(prompt)

            if len(questions) >= num_questions:
                break

        return questions
