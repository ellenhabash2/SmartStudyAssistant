# RAG Experimentation Results
## Experiment Summary
- **Total configurations tested**: 1
- **Dataset**: local
- **Evaluation questions**: 10
- **Vector store backend(s)**: memory
- **Retrieval options**: semantic, BM25, hybrid fusion, optional reranking
- **Generation mode(s)**: grounded

## Results by Configuration
| Chunk Size | Strategy | Vector Store | Retrieval | Generation | Top-K | Accuracy | Precision@K | Recall@K | MRR | NDCG | Grounding | Hallucination | Citation Cov. | Ctx Use | Resp. Time (ms) | Num Chunks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 300 | recursive | memory | semantic | grounded | 3 | 0.092 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.5 | 65 |

## Aggregate Metrics
- **Evaluated question/configuration pairs**: 10
- **Average accuracy**: 0.092
- **Average Precision@K**: 0.000
- **Average Recall@K**: 0.000
- **Average grounding score**: 1.000
- **Average hallucination rate**: 0.000
- **Average citation coverage**: 1.000
- **Average context usage rate**: 1.000
- **Average response time**: 1.5 ms
- **Question-level errors**: 0

## Key Findings
**Best Accuracy**: chunk_size=300, overlap=30, top_k=3, provider=mock, chunking=recursive, retrieval=semantic, vector_store=memory, generation=grounded
- Accuracy: 0.092

**Best Grounding**: chunk_size=300, overlap=30, top_k=3, provider=mock, chunking=recursive, retrieval=semantic, vector_store=memory, generation=grounded
- Grounding Score: 1.000

**Fastest**: chunk_size=300, overlap=30, top_k=3, provider=mock, chunking=recursive, retrieval=semantic, vector_store=memory, generation=grounded
- Response Time: 1.5ms

## Analysis & Recommendations
### Chunk Size Impact
- Smaller chunks enable more precise retrieval
- Larger chunks provide more context
- Trade-off between specificity and information richness

### Top-K Impact
- Higher top-k values improve coverage but reduce speed
- Baseline performance depends on document structure

### Baseline Comparison
- Semantic retrieval should outperform keyword search when embeddings are meaningful
- Large improvements over random suggest embedding quality

### Failures & Limitations
- Mock embeddings are deterministic but not semantically strong
- Current generated answers are retrieved chunks, not polished LLM responses
- RAGBench includes multimodal references; this prototype currently evaluates text/table text only

## Recommended Configuration
Based on accuracy and grounding, recommend:
- Chunk Size: 300
- Overlap: 30
- Top-K: 3
