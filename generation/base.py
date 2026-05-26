from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class RetrievedContext:
    """Retrieved chunk plus retrieval metadata used for generation."""

    chunk_id: str
    text: str
    score: float
    source: str = ""
    page_number: int | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Citation:
    """Citation rendered in answers and benchmark artifacts."""

    chunk_id: str
    label: str
    source: str
    page_number: int | None
    score: float


@dataclass(frozen=True)
class GenerationContext:
    """Inputs passed from retrieval into the generation layer."""

    question: str
    contexts: list[RetrievedContext]
    show_citations: bool = True


@dataclass(frozen=True)
class GenerationResult:
    """Structured grounded generation output."""

    answer: str
    citations: list[Citation]
    used_chunk_ids: list[str]
    confidence: float
    weak_context_warning: str | None = None
    provider: str = "mock"
    prompt: str = ""


class LLMClient(Protocol):
    """Minimal interface for optional LLM-backed answer generation."""

    provider_name: str

    def generate(self, prompt: str) -> str:
        """Generate answer text from an already-grounded prompt."""
