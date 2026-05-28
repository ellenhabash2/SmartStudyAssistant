# RAG Experimentation Results
## Experiment Summary
- **Total configurations tested**: 9
- **Dataset**: ragbench
- **Evaluation questions**: 10
- **Vector store**: in-memory cosine similarity

## Results by Configuration
| Chunk Size | Overlap | Top-K | Accuracy | Precision@K | Grounding | Resp. Time (ms) | Num Chunks |
|---|---|---|---|---|---|---|---|
| 500 | 50 | 3 | 0.065 | 0.000 | 1.000 | 64.9 | 3025 |
| 300 | 30 | 3 | 0.080 | 0.000 | 1.000 | 116.4 | 5011 |
| 800 | 80 | 3 | 0.043 | 0.000 | 1.000 | 43.4 | 1917 |
| 500 | 50 | 1 | 0.083 | 0.000 | 1.000 | 68.7 | 3025 |
| 500 | 50 | 5 | 0.055 | 0.000 | 1.000 | 60.4 | 3025 |
| 300 | 30 | 5 | 0.067 | 0.000 | 1.000 | 102.3 | 5011 |
| 800 | 80 | 1 | 0.061 | 0.000 | 1.000 | 43.2 | 1917 |
| 500 | 50 | 3 | 0.170 | 0.000 | 1.000 | 38.7 | 3025 |
| 500 | 50 | 3 | 0.075 | 0.000 | 1.000 | 38.0 | 3025 |

## Aggregate Metrics
- **Evaluated question/configuration pairs**: 90
- **Average accuracy**: 0.078
- **Average Precision@K**: 0.000
- **Average grounding score**: 1.000
- **Average response time**: 64.0 ms
- **Question-level errors**: 0

## Key Findings
**Best Accuracy**: chunk_size=500, overlap=50, top_k=3, provider=mock
- Accuracy: 0.170

**Best Grounding**: chunk_size=500, overlap=50, top_k=3, provider=mock
- Grounding Score: 1.000

**Fastest**: chunk_size=500, overlap=50, top_k=3, provider=mock
- Response Time: 38.0ms

**Lowest Accuracy**: chunk_size=800, overlap=80, top_k=3, provider=mock
- Accuracy: 0.043

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
- Chunk Size: 500
- Overlap: 50
- Top-K: 3
