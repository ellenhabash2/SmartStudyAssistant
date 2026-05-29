"""
Streamlit UI for Smart Study Assistant.

The app uses a LangChain-based RAG flow for PDF processing, retrieval,
deterministic grounded answers, and quiz generation.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import streamlit as st

from rag import LangChainDependencyError, LangChainPipelineError, LangChainRAGPipeline
from services.quiz_service import QuizService


st.set_page_config(
    page_title="Smart Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_state() -> None:
    defaults = {
        "pdf_loaded": False,
        "pdf_name": "",
        "rag_pipeline": None,
        "rag_stats": {},
        "page_documents": [],
        "chunk_documents": [],
        "quiz_questions": [],
        "embedding_model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "use_mock_embeddings": False,
        "chunk_size": 500,
        "chunk_overlap": 50,
        "top_k": 3,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def build_pipeline() -> LangChainRAGPipeline:
    model_name = "mock" if st.session_state.use_mock_embeddings else st.session_state.embedding_model_name.strip()
    return LangChainRAGPipeline(
        embedding_model_name=model_name,
        chunk_size=st.session_state.chunk_size,
        chunk_overlap=st.session_state.chunk_overlap,
        top_k=st.session_state.top_k,
    )


def process_uploaded_pdf(uploaded_file: Any) -> dict[str, Any]:
    if uploaded_file is None:
        return {"success": False, "message": "Choose a PDF file before processing."}

    try:
        pipeline = build_pipeline()
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / uploaded_file.name
            temp_path.write_bytes(uploaded_file.getbuffer())
            stats = pipeline.process_pdf(str(temp_path))

        st.session_state.pdf_loaded = True
        st.session_state.pdf_name = uploaded_file.name
        st.session_state.rag_pipeline = pipeline
        st.session_state.rag_stats = stats
        st.session_state.page_documents = pipeline.documents
        st.session_state.chunk_documents = pipeline.chunks
        st.session_state.quiz_questions = []
        return {"success": True, "message": f"Processed {uploaded_file.name}", "stats": stats}

    except (LangChainDependencyError, LangChainPipelineError) as error:
        st.session_state.pdf_loaded = False
        st.session_state.rag_pipeline = None
        st.session_state.rag_stats = {}
        st.session_state.page_documents = []
        st.session_state.chunk_documents = []
        return {"success": False, "message": str(error)}
    except Exception as error:
        st.session_state.pdf_loaded = False
        st.session_state.rag_pipeline = None
        st.session_state.rag_stats = {}
        st.session_state.page_documents = []
        st.session_state.chunk_documents = []
        return {"success": False, "message": f"Unexpected error while processing the PDF: {error}"}


def answer_question(query: str) -> dict[str, Any]:
    pipeline = st.session_state.rag_pipeline
    if not st.session_state.pdf_loaded or pipeline is None:
        return {"success": False, "message": "Please process a PDF before asking questions."}

    try:
        result = pipeline.answer_question(query)
        return {"success": True, **result}
    except (LangChainDependencyError, LangChainPipelineError) as error:
        return {"success": False, "message": str(error)}
    except Exception as error:
        return {"success": False, "message": f"Unexpected error while answering the question: {error}"}


def generate_quiz() -> list[dict[str, Any]]:
    if not st.session_state.pdf_loaded:
        return []

    questions = QuizService.generate_from_documents(st.session_state.chunk_documents, num_questions=3)
    st.session_state.quiz_questions = questions
    return [
        {
            "prompt": question.prompt,
            "options": question.options,
            "answer": question.answer,
            "citation": question.citation,
        }
        for question in questions
    ]


def show_processing_stats(stats: dict[str, Any]) -> None:
    columns = st.columns(5)
    columns[0].metric("Pages", stats.get("pages", 0))
    columns[1].metric("Chunks", stats.get("chunks", 0))
    columns[2].metric("Embedding Model", stats.get("embedding_model", ""))
    columns[3].metric("Chunk Size", stats.get("chunk_size", 0))
    columns[4].metric("Overlap", stats.get("chunk_overlap", 0))


def page_label(document: Any) -> str:
    metadata = dict(getattr(document, "metadata", {}) or {})
    page = metadata.get("page")
    return f"Page {page}" if page else "Page"


initialize_state()

with st.sidebar:
    st.header("RAG Settings")
    st.session_state.chunk_size = st.slider("Chunk size", min_value=200, max_value=1200, value=st.session_state.chunk_size, step=50)
    st.session_state.chunk_overlap = st.slider(
        "Chunk overlap",
        min_value=0,
        max_value=min(300, st.session_state.chunk_size - 1),
        value=min(st.session_state.chunk_overlap, st.session_state.chunk_size - 1),
        step=10,
    )
    st.session_state.top_k = st.slider("Top K", min_value=1, max_value=8, value=st.session_state.top_k, step=1)
    st.session_state.embedding_model_name = st.text_input(
        "Embedding model",
        value=st.session_state.embedding_model_name,
        help="Default: sentence-transformers/all-MiniLM-L6-v2",
    )
    st.session_state.use_mock_embeddings = st.checkbox(
        "Use mock embeddings",
        value=st.session_state.use_mock_embeddings,
        help="Keep this on for fully offline demos or if model download is unavailable.",
    )

    st.markdown("---")
    if st.session_state.pdf_loaded:
        st.success(f"Loaded: {st.session_state.pdf_name}")
    else:
        st.info("No PDF processed yet.")

st.markdown(
    """
    <div style="text-align:center; margin-bottom: 1rem;">
        <h1>📚 Smart Study Assistant</h1>
        <p style="color:#555;">LangChain-based PDF RAG for grounded study support.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

upload_tab, ask_tab, quiz_tab, ocr_tab, benchmark_tab, about_tab = st.tabs(
    [
        "📄 Upload PDF",
        "❓ Ask Questions",
        "📝 Generate Quiz",
        "🔎 OCR / Text",
        "📊 Benchmark Results",
        "ℹ️ About",
    ]
)

with upload_tab:
    st.header("Upload PDF")
    st.write("Upload a PDF and process it with the LangChain RAG pipeline.")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if st.button("Process PDF", disabled=uploaded_file is None):
        with st.spinner("Loading PDF, splitting text, and building FAISS index..."):
            result = process_uploaded_pdf(uploaded_file)
        if result["success"]:
            st.success(result["message"])
        else:
            st.error(result["message"])

    if st.session_state.pdf_loaded:
        st.subheader("Current Document Stats")
        show_processing_stats(st.session_state.rag_stats)
        if st.session_state.use_mock_embeddings:
            st.caption("Mock embeddings are active. Switch them off to use HuggingFace embeddings with FAISS.")
        else:
            st.caption("The first HuggingFace model load may take a while because the model is downloaded locally.")

with ask_tab:
    st.header("Ask Questions")
    if not st.session_state.pdf_loaded:
        st.info("Upload and process a PDF first.")
    else:
        query = st.text_input("Enter a question about the document")
        if st.button("Get Answer"):
            if not query.strip():
                st.warning("Enter a question before submitting.")
            else:
                with st.spinner("Retrieving grounded context..."):
                    answer_data = answer_question(query)

                if answer_data["success"]:
                    st.markdown("### Answer")
                    st.write(answer_data["answer"])

                    if answer_data["citations"]:
                        st.markdown("### Citations")
                        for citation in answer_data["citations"]:
                            st.write(f"- {citation}")

                    st.markdown("### Retrieved Chunks")
                    for index, chunk in enumerate(answer_data["retrieved_chunks"], start=1):
                        label = f"Chunk {index} • {chunk['source']}"
                        if chunk.get("page"):
                            label += f" • page {chunk['page']}"
                        with st.expander(label):
                            if chunk.get("score") is not None:
                                st.caption(f"Score: {chunk['score']:.4f}")
                            st.write(chunk["text"])
                else:
                    st.error(answer_data["message"])

with quiz_tab:
    st.header("Generate Quiz")
    if not st.session_state.pdf_loaded:
        st.info("Upload and process a PDF before generating a quiz.")
    else:
        if st.button("Create Quiz"):
            generate_quiz()

        if st.session_state.quiz_questions:
            for index, item in enumerate(st.session_state.quiz_questions, start=1):
                st.markdown(f"### Question {index}")
                st.write(item.prompt)
                for option_index, option in enumerate(item.options, start=1):
                    st.write(f"{option_index}. {option}")
                st.write(f"**Answer:** {item.answer}")
                if item.citation:
                    st.caption(f"Citation: {item.citation}")
        else:
            st.info("Create a quiz after processing a document.")

with ocr_tab:
    st.header("OCR / Text")
    if not st.session_state.pdf_loaded:
        st.info("Upload and process a PDF to inspect extracted text.")
    else:
        st.write("The LangChain loader output is shown page by page.")
        for document in st.session_state.page_documents:
            with st.expander(page_label(document), expanded=False):
                st.write(getattr(document, "page_content", "") or "(No text extracted from this page)")

with benchmark_tab:
    st.header("Benchmark Results")
    st.write("The benchmark runner supports both the legacy flow and the LangChain UI backend.")
    st.code(
        "python main_experiment.py --dataset local --rag-backend langchain "
        "--embedding-model sentence-transformers/all-MiniLM-L6-v2 "
        "--chunk-size 500 --overlap 50 --top-k 3"
    )
    st.write("Benchmark outputs are written to the `results/` folder.")
    st.caption("If the LangChain dependencies are not installed yet, the legacy benchmark remains available.")

with about_tab:
    st.header("About")
    st.markdown(
        """
        Smart Study Assistant is a clean demo RAG platform for studying PDF documents.

        - LangChain loads and splits PDFs
        - HuggingFace embeddings power local semantic retrieval
        - FAISS stores vectors in memory
        - Answers stay grounded in retrieved chunks and include citations
        - Quiz generation reuses the processed document chunks
        """
    )
    st.markdown("### Notes")
    st.write("Use text-based PDFs for the best results. Scanned PDFs may need OCR before retrieval works well.")
    st.write("If the local embedding model download is slow or unavailable, switch on mock embeddings for an offline fallback.")

st.markdown("---")
st.write("Smart Study Assistant — clean and stable LangChain RAG demo.")
