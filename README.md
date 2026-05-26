# Smart Study Assistant - RAG-Based PDF Learning System

## Overview

Smart Study Assistant is a prototype Retrieval-Augmented Generation (RAG) system for asking questions about PDF study materials. The project extracts text from PDFs, chunks the content, embeds the chunks, retrieves relevant context, and returns an answer grounded in the retrieved material.

The project is currently an MVP for academic experimentation. It is designed to make RAG design choices visible and measurable, especially chunk size, chunk overlap, Top-K retrieval depth, embedding provider, retrieval quality, grounding, and response time.

## Problem Statement

Students often need to review long PDFs, lecture notes, and technical readings quickly. Standard keyword search can miss relevant explanations when the wording differs from the student's question. This project explores how a RAG pipeline can help students ask natural-language questions and receive answers based on the source document.

## Main Features

- PDF text extraction using PyMuPDF with pypdf fallback
- Configurable document chunking with overlap
- Mock embeddings for offline reproducible experiments
- SentenceTransformers, BGE, E5, Hugging Face, and OpenAI embedding providers
- Optional OpenAI embeddings when `OPENAI_API_KEY` is configured
- Pluggable vector stores: memory by default, FAISS, ChromaDB, and Qdrant support
- Persistent vector indexes, metadata filtering, incremental updates, and deletion
- Semantic, BM25, and hybrid retrieval with optional reranking
- Retrieval service for Top-K context lookup
- Simple QA service and grounded generation layer for citation-aware answers
- CLI demo
- Simple web UI for asking questions over PDFs in `data/`
- Experiment runner for comparing RAG configurations
- Local evaluation dataset support
- Vectara Open RAG Benchmark support through Hugging Face

## Current Implementation Status

The system works as a research-oriented RAG platform. The default configuration still uses mock embeddings so smoke tests and demos can run without paid APIs or internet access after dependencies are installed. Real semantic embedding providers are available for stronger retrieval experiments.

The default vector store is an in-memory cosine-similarity store with JSON persistence. FAISS, ChromaDB, and Qdrant backends are available through the same vector store interface; optional dependencies are loaded only when those backends are selected.

Answers can run in two modes. The backward-compatible default returns retrieved chunks directly for retrieval experiments. The grounded generation mode builds citation-aware answers from retrieved evidence, uses a deterministic mock generator offline, and can use OpenAI when `OPENAI_API_KEY` is available.

## Architecture

```text
PDF / Benchmark Data
        |
        v
PDF extraction or RAGBench loader
        |
        v
ChunkService
        |
        v
EmbeddingService
        |
        v
VectorStoreService
        |
        v
RetrievalService
        |
        v
AnswerGenerator
        |
        v
Citations / Evaluation
```

## How the RAG Pipeline Works

1. The system loads text from a PDF or benchmark dataset.
2. Text is split into overlapping chunks.
3. Each chunk is converted into an embedding vector.
4. A question is embedded using the same embedding provider.
5. The vector store retrieves the Top-K most similar chunks.
6. The generation layer either returns retrieved chunks or produces a grounded answer with citations.
7. The experiment runner compares the generated answer, citations, and retrieved context against evaluation data.

## Project Structure

```text
app/
  main.py                  CLI demo
  web.py                   Simple web UI
core/
  config.py                Default configuration
  models.py                Shared data models
data/
  evaluation/              Local and benchmark notes
  example.pdf              Example source PDF
embeddings/
  providers.py             Mock, OpenAI, and SentenceTransformers providers
retrieval/
  hybrid.py                BM25 and weighted hybrid retrieval
reranking/
  rerankers.py             Heuristic and CrossEncoder rerankers
generation/
  base.py                  Generation data contracts
  prompt_builder.py        Grounded prompt construction
  citation_formatter.py    Source and page citation labels
  answer_generator.py      Grounded answer orchestration
  mock_llm.py              Deterministic offline LLM fallback
  openai_llm.py            Optional OpenAI generation
services/
  chunk_service.py         Text chunking
  dataset_loader.py        Local evaluation dataset loading
  ragbench_loader.py       Vectara Open RAG Benchmark loading
  embedding_service.py     Embedding service facade
  vector_store_service.py  Backward-compatible default vector store
  retrieval_service.py     Query retrieval
  qa_service.py            Answer construction
  evaluation_service.py    Metrics
  experiment_runner.py     Experiment orchestration
vectorstores/
  factory.py               Vector store backend selection
  memory.py                Persistent local JSON vector store
  faiss_store.py           FAISS backend
  chroma_store.py          ChromaDB backend
  qdrant_store.py          Qdrant backend
results/
  *.csv, *.md              Experiment outputs
main_experiment.py         Experiment CLI
requirements.txt           Python dependencies
```

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

For OpenAI embeddings:

```bash
export OPENAI_API_KEY="your-api-key"
```

## How to Run CLI Demo

```bash
python app/main.py
```

## How to Run Web UI

```bash
python app/web.py
```

Then open the local URL printed by the script, usually:

```text
http://localhost:8000
```

## How to Run Local Experiments

```bash
python main_experiment.py --dataset local
```

Run one local configuration:

```bash
python main_experiment.py --dataset local --chunk-size 500 --top-k 3
```

Compare hybrid retrieval with reranking:

```bash
python main_experiment.py \
  --dataset local \
  --chunk-size 300 \
  --top-k 3 \
  --retrieval-mode hybrid \
  --reranker heuristic
```

Use a persistent local vector index:

```bash
python main_experiment.py \
  --dataset local \
  --chunk-size 300 \
  --top-k 3 \
  --vector-store memory \
  --vector-store-path .vectorstores/local_memory.json
```

Use FAISS for semantic search:

```bash
python main_experiment.py \
  --dataset local \
  --vector-store faiss \
  --vector-store-path .vectorstores/local_faiss.pkl
```

Run grounded generation with citations:

```bash
python main_experiment.py \
  --dataset local \
  --chunk-size 300 \
  --top-k 3 \
  --generation-mode grounded \
  --llm-provider mock \
  --show-citations
```

Use OpenAI generation when `OPENAI_API_KEY` is configured:

```bash
python main_experiment.py \
  --dataset local \
  --generation-mode grounded \
  --llm-provider openai \
  --show-citations
```

Results are written to:

```text
results/experiment_results.csv
results/experiment_summary.md
```

## How to Run RAGBench Experiments

Fast test with 10 examples:

```bash
python main_experiment.py --dataset ragbench --limit 10
```

Run one RAGBench configuration:

```bash
python main_experiment.py --dataset ragbench --limit 50 --chunk-size 500 --top-k 3
```

If you already downloaded the dataset locally:

```bash
python main_experiment.py \
  --dataset ragbench \
  --open-rag-bench-path data/open-rag-bench/pdf/arxiv \
  --limit 50
```

Results are written to:

```text
results/ragbench_results.csv
results/ragbench_summary.md
```

## Dataset Strategy

The original project used a small manually written evaluation dataset. That is useful for early development, but it is limited and can be biased toward a small number of examples.

We use Vectara Open RAG Benchmark because it provides realistic PDF-based RAG evaluation data. It helps us test retrieval quality, grounding, chunk size, Top-K, and embedding model choices using a more objective benchmark instead of only manually written questions.

Open RAG Benchmark is available from:

- GitHub: https://github.com/vectara/open-rag-bench
- Hugging Face: https://huggingface.co/datasets/vectara/open_ragbench

The benchmark includes PDF-derived scientific content, question-answer pairs, document/section relevance labels, and data involving text, tables, and image-related content. This project currently uses the text and table text portions that can be represented in the existing text-based RAG pipeline.

## Evaluation Metrics

- **Accuracy**: token-level F1 overlap between generated and expected answer
- **Precision@K**: how often retrieved chunks contain the expected source text
- **Recall@K**: whether any top-K chunk contains the expected source text
- **MRR**: how highly the first relevant chunk is ranked
- **NDCG**: ranking quality using binary relevance labels
- **Grounding score**: how much of the generated answer appears in retrieved context
- **Hallucination rate**: estimated ungrounded answer-token rate
- **Answer relevancy**: placeholder lexical overlap between question and answer
- **Citation coverage**: how many used evidence chunks are cited
- **Context usage rate**: how much of the retrieved context the generator used
- **Response time**: how long retrieval and answer construction took

## Grounded Generation

The old answer path is still available as `--generation-mode retrieved_chunks`. It is useful for pure retrieval benchmarking because the answer is just the retrieved evidence.

The new `--generation-mode grounded` path adds a modular generation layer:

- Builds a grounded prompt from the question and retrieved chunks
- Tracks chunk IDs, source IDs, page numbers, retrieval scores, and metadata
- Produces answer text, citations, used chunk IDs, confidence, and weak-context warnings
- Falls back to deterministic mock generation when no API key is available
- Uses OpenAI only when `--llm-provider openai` and `OPENAI_API_KEY` are both present

Before this phase, answers were mostly raw chunks. After this phase, experiments can compare raw retrieval against citation-aware grounded answers while preserving reproducibility.

## What Works

- End-to-end PDF question answering prototype
- Offline experiments with mock embeddings
- Optional OpenAI and local SentenceTransformers embedding support
- Multiple chunking strategies: recursive, sentence, token-aware, sliding window, semantic, parent-child
- Multiple vector store backends: memory, FAISS, ChromaDB, Qdrant
- Metadata filtering, persistence, incremental updates, and deletion in the vector store layer
- Semantic, BM25, and hybrid retrieval with optional heuristic reranking
- Grounded generation with citations, confidence, and weak-context warnings
- Optional OpenAI generation with deterministic mock fallback
- Robust local evaluation loading that skips malformed records
- RAGBench loading through Hugging Face or local downloaded files
- Per-question CSV experiment outputs
- Markdown summaries for reports
- Unit tests for the vector store contract and grounded generation behavior

## Current Limitations

- Mock embeddings are useful for smoke tests but not a replacement for real semantic embeddings
- ChromaDB and Qdrant wrappers require optional packages and are not exercised by default smoke tests
- OpenAI generation is optional and depends on `OPENAI_API_KEY`; offline runs use deterministic mock generation
- RAGBench contains multimodal data, but this prototype primarily evaluates text/table text
- Hugging Face dataset loading requires internet access unless the dataset is already downloaded
- Large RAGBench runs can be slow because this MVP rebuilds embeddings for each configuration

## Future Improvements

- Add streaming LLM responses and richer prompt templates
- Improve citation UX in the web interface
- Add multimodal handling for RAGBench images
- Add stronger semantic metrics such as BERTScore or LLM-as-judge evaluation
- Add Streamlit benchmark dashboard and retrieval visualizations
- Add automated tests for loaders, metrics, generation, and experiment output formats

## Example Commands

```bash
python app/main.py
python app/web.py
python main_experiment.py --dataset local
python main_experiment.py --dataset local --chunk-size 300 --top-k 5
python main_experiment.py --dataset local --retrieval-mode hybrid --reranker heuristic
python main_experiment.py --dataset local --generation-mode grounded --llm-provider mock --show-citations
python main_experiment.py --dataset local --vector-store faiss --vector-store-path .vectorstores/local_faiss.pkl
python main_experiment.py --dataset ragbench --limit 10
python main_experiment.py --dataset ragbench --limit 50 --embedding-provider openai
```

## Team Members

- Ellen Habash
- Nechami Rabinovitz
