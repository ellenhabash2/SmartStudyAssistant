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
- Optional OpenAI embeddings when `OPENAI_API_KEY` is configured
- In-memory cosine-similarity vector search
- Retrieval service for Top-K context lookup
- Simple QA service that builds answers from retrieved chunks
- CLI demo
- Simple web UI for asking questions over PDFs in `data/`
- Experiment runner for comparing RAG configurations
- Local evaluation dataset support
- Vectara Open RAG Benchmark support through Hugging Face

## Current Implementation Status

The system works as a prototype/MVP. The default configuration uses mock embeddings so the project can run without paid APIs or internet access after dependencies are installed. Mock embeddings are deterministic and useful for testing the pipeline, but they are not semantically strong.

The current vector store is an in-memory cosine-similarity store. FAISS is a reasonable future improvement, but this version does not require FAISS to run.

Answers are currently based on retrieved chunks unless a future LLM generation layer is enabled. This makes the system useful for retrieval and grounding experiments, but the answers may read like excerpts rather than polished tutoring responses.

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
QA / Evaluation
```

## How the RAG Pipeline Works

1. The system loads text from a PDF or benchmark dataset.
2. Text is split into overlapping chunks.
3. Each chunk is converted into an embedding vector.
4. A question is embedded using the same embedding provider.
5. The vector store retrieves the Top-K most similar chunks.
6. The current QA layer returns an answer based on retrieved chunks.
7. The experiment runner compares the generated answer and retrieved context against evaluation data.

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
services/
  chunk_service.py         Text chunking
  dataset_loader.py        Local evaluation dataset loading
  ragbench_loader.py       Vectara Open RAG Benchmark loading
  embedding_service.py     Mock/OpenAI embeddings
  vector_store_service.py  In-memory vector search
  retrieval_service.py     Query retrieval
  qa_service.py            Answer construction
  evaluation_service.py    Metrics
  experiment_runner.py     Experiment orchestration
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
- **Grounding score**: how much of the generated answer appears in retrieved context
- **Response time**: how long retrieval and answer construction took

## What Works

- End-to-end PDF question answering prototype
- Offline experiments with mock embeddings
- Optional OpenAI embedding support
- Robust local evaluation loading that skips malformed records
- RAGBench loading through Hugging Face or local downloaded files
- Per-question CSV experiment outputs
- Markdown summaries for reports

## Current Limitations

- Mock embeddings are not a replacement for real semantic embeddings
- The vector store is in-memory and intended for small experiments
- Answers are currently retrieved-context based, not full LLM-generated tutoring answers
- RAGBench contains multimodal data, but this prototype primarily evaluates text/table text
- Hugging Face dataset loading requires internet access unless the dataset is already downloaded
- Large RAGBench runs can be slow because this MVP rebuilds embeddings for each configuration

## Future Improvements

- Add FAISS or another persistent vector database
- Add an LLM generation step for natural answers
- Improve citation support with document IDs and section metadata
- Add multimodal handling for RAGBench images
- Cache embeddings between experiment runs
- Add stronger semantic metrics such as BERTScore or LLM-as-judge evaluation
- Add automated tests for loaders, metrics, and experiment output formats

## Example Commands

```bash
python app/main.py
python app/web.py
python main_experiment.py --dataset local
python main_experiment.py --dataset local --chunk-size 300 --top-k 5
python main_experiment.py --dataset ragbench --limit 10
python main_experiment.py --dataset ragbench --limit 50 --embedding-provider openai
```

## Team Members

- Ellen Habash
- Nechami Rabinovitz
