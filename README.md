# Smart Study Assistant — RAG Platform

Smart Study Assistant is a clean, demo-ready PDF question answering app with a LangChain-based RAG pipeline.

## What the app does
- Upload a PDF document
- Load document pages with LangChain
- Split text with `RecursiveCharacterTextSplitter`
- Create semantic embeddings with `sentence-transformers/all-MiniLM-L6-v2`
- Store vectors in FAISS
- Retrieve grounded context for question answering
- Return answers with citations
- Generate simple document-based quiz questions

## LangChain-based RAG Pipeline
The main app flow now uses LangChain for the core retrieval pipeline:

`PDF -> PyPDFLoader -> RecursiveCharacterTextSplitter -> HuggingFaceEmbeddings -> FAISS -> Retriever -> Grounded Answer with Citations`

- LangChain loads PDFs page by page
- `RecursiveCharacterTextSplitter` creates overlapping chunks
- HuggingFace `all-MiniLM-L6-v2` embeddings provide real semantic retrieval
- FAISS stores vectors in memory
- The retriever finds relevant chunks
- The app answers only from retrieved context and shows citations

Mock embeddings are still available for offline demos and testing.

## Installation
```bash
pip install -r requirements.txt
```

## Running the app
```bash
streamlit run ui/streamlit_app.py
```

The first run may download the HuggingFace model.

## Running the benchmark
Legacy benchmark:

```bash
python main_experiment.py --dataset local
```

LangChain UI-aligned benchmark:

```bash
python main_experiment.py --dataset local --rag-backend langchain --embedding-model sentence-transformers/all-MiniLM-L6-v2 --chunk-size 500 --overlap 50 --top-k 3
```

Benchmark outputs are written to `results/benchmark_results.csv` and `results/benchmark_summary.md`.

## Using the app
1. Run the Streamlit UI.
2. Upload a text-based PDF.
3. Adjust chunk size, overlap, top-k, and embedding model from the sidebar if needed.
4. Process the PDF.
5. Ask a question in the `Ask Questions` tab.
6. Review citations and retrieved chunks.
7. Generate a quiz from the processed document if needed.

## Troubleshooting
- `sentence-transformers` install issue:
  Reinstall with `pip install -r requirements.txt`. Some systems need an updated `pip`, `setuptools`, and `wheel`.
- `faiss-cpu` install issue:
  Use a supported Python version and platform wheel. If FAISS is unavailable temporarily, the app cannot build the LangChain vector store.
- Slow first model download:
  The first HuggingFace model load can take time because the model is downloaded locally.
- Weak answer quality:
  Reprocess the PDF after changing chunk settings or the embedding model.
- No internet or model download blocked:
  Enable mock embeddings from the sidebar to keep the demo running without real embeddings.

## Notes
- The Streamlit UI uses the LangChain RAG pipeline.
- The legacy benchmark path still exists for compatibility.
- Text-based PDFs work best. Scanned PDFs may need OCR before retrieval becomes reliable.
