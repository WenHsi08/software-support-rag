# Software Support RAG Assistant

A command-line retrieval-augmented generation (RAG) prototype for software
troubleshooting. It accepts natural-language questions, retrieves simulated
support documentation, and generates Traditional Chinese answers using Gemini.

The project focuses on understanding retrieval, document-grounded answers,
modular system design, and evaluation. The current knowledge base describes
HelpDesk Lite, a simulated application.

## Current Features

- Load Markdown files from `docs/`, including subfolders.
- Split documents by second-level headings and classify chunks as
  `issue`, `guide`, `support`, `scope`, `overview`, or `general`.
- Generate 3072-dimensional vectors using `gemini-embedding-001`, with
  `RETRIEVAL_DOCUMENT` and `RETRIEVAL_QUERY` task types.
- Calculate cosine similarity in Python and rank document chunks.
- Select matching issue sections for explicit error codes.
- For questions without a recognised code pattern, select the top two eligible
  semantic results, excluding `scope` and `overview`.
- Add support procedures and scope information from the selected sources,
  removing duplicate chunks.
- Cache document chunks and embeddings in SQLite. Reuse cached vectors when
  document content, chunk content and classification, model, and dimensions match.
- Generate answers with source IDs and filenames.
- Return a local clarification message when explicit codes have no matching
  issue sections, without calling the answer-generation model.

## How It Works

1. Load and classify document chunks.
2. Load document vectors from SQLite, or generate and save them if the cache
   is missing or no longer matches.
3. Accept a question and generate its query vector.
4. Calculate similarity scores for all chunks.
5. Select reference material:
   - **Explicit code:** select issue chunks with matching heading codes.
     Record unmatched codes separately.
   - **No code:** select the top two eligible chunks by semantic similarity.
6. Add same-source support and scope chunks to the context.
7. Generate a document-grounded answer, or return a local clarification message
   if no chunks were selected.

The current code pattern is one ASCII letter followed by three digits, such as
`E202`. Matching is case-insensitive. Exact selection uses issue headings,
rather than mentions of a code elsewhere in a document.

All non-empty questions currently go through query embedding and similarity
calculation before selection, including questions with explicit codes. Skipping
these operations for code-only lookups is a future optimisation.

## Tech Stack

- Python 3.11
- Google GenAI SDK and Gemini API
- Gemini Embedding
- SQLite through Python's built-in `sqlite3`
- Cosine similarity implemented in Python
- Markdown knowledge documents
- Git and GitHub

SQLite stores the vectors. Similarity search runs in Python, without a vector
index or dedicated vector database.

## Getting Started

The following commands are for Windows PowerShell.

### 1. Clone the repository

```powershell
git clone https://github.com/WenHsi08/software-support-rag.git
cd software-support-rag
```

If these features have not yet been merged into `main`, switch to the development
branch:

```powershell
git switch feature/vector-search
```

### 2. Create and activate a virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install the dependency

```powershell
python -m pip install google-genai
```

SQLite and the other standard-library modules do not require separate installation.

### 4. Set your API key

Create a Gemini API key in Google AI Studio, then set it in the current terminal:

```powershell
$env:GEMINI_API_KEY = "YOUR_API_KEY"
```

Do not commit API keys. Set this variable again when opening a new terminal.

### 5. Check the model configuration

The current configuration in `test_embedding.py` is:

```python
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 3072
ANSWER_MODEL = "gemini-3.8-flash"
```

Use an answer model available to your account. `check_models.py` lists models
that support content generation. Model availability and quotas depend on the provider.

### 6. Run the assistant

```powershell
python test_embedding.py
```

Despite its filename, this is currently the main manual entry point for the
integrated retrieval and answer workflow, not an automated test suite.
Each run accepts one question.

The first run creates `data/knowledge.db` and generates document embeddings.
Subsequent runs reuse matching document vectors. The `data/` directory is
excluded from Git.

Document text and questions are sent to the configured embedding API when
vectors are generated. Selected context and the question are sent to the
answer-generation API when an LLM answer is requested. Use the simulated
documents for this prototype.

## Manually Verified Scenarios

| Input | Observed behaviour |
| --- | --- |
| 有錯誤 E202 怎麼辦？ | Selects the E202 issue section, adds support and scope information, and generates the documented permission-request steps. |
| 有錯誤 W202 怎麼辦？ | Reports that W202 is not documented and requests clarification. Does not substitute E202 or call the answer-generation model. |
| 我沒有權限匯出報表。 | Uses semantic retrieval and generates the permission-request procedure without presenting E201's date restriction as the cause. |

These are initial manual checks against one simulated document, not a comprehensive
evaluation. Query embedding still calls the API in the unknown-code scenario.

## Project Files

| File | Purpose |
| --- | --- |
| `test_embedding.py` | CLI workflow, embedding configuration, caching, retrieval, and answer integration |
| `knowledge_base.py` | Markdown loading, heading-based chunking, and rule-based classification |
| `retriever.py` | Cosine similarity, ranking, exact-code selection, and semantic result selection |
| `context_builder.py` | Selected chunks plus same-source support and scope information |
| `storage.py` | SQLite initialisation, document/vector storage, and cache validation |
| `answerer.py` | Local fallback responses, prompt construction, and Gemini answer generation |
| `read_docs.py` | Earlier error-code retrieval and answer prototype |
| `check_models.py` | List models supporting content generation |
| `test_llm.py` | Basic manual LLM API check |
| `docs/report_export.md` | KB-001: simulated report-export troubleshooting documentation |

SQLite uses `documents`, `chunks`, and `embeddings` tables. Embeddings are stored
as JSON text, with their model name and dimensions.

## Current Limitations

- The knowledge base contains one simulated document covering E201 and E202.
- Semantic selection uses a fixed Top-2 with no similarity threshold. The second
  result may be irrelevant, and unrelated questions can still retrieve candidates.
- Unknown explicit codes currently block semantic fallback when no known code
  matches, even if the question also includes a useful symptom description.
- Code selection does not yet distinguish identical codes across products or versions.
- Chunk classification depends on heading conventions, rather than general
  document understanding.
- There is no conversation history, input loop, API service, or web interface.
- API failures are not yet handled gracefully.
- Prompt rules guide answers but do not guarantee factual correctness or
  protection against prompt injection.
- The assistant does not create tickets, log unresolved cases, submit requests,
  or change permissions.
- Automated tests and broader retrieval/answer evaluation have not yet been added.

## Planned Improvements

- Expand the knowledge base and evaluate ambiguous, unrelated, and mixed-code questions.
- Evaluate retrieval relevance, answer faithfulness, completeness, and source attribution.
- Compare baseline prompts with explicit writing rules inspired by Simplified
  Technical English (STE). Traditional Chinese output will not be described as
  ASD-STE100 compliant.
- Refine Top-k selection, thresholds, and unknown-code handling based on evaluation.
- Add error handling and automated tests.
- Build a FastAPI backend and a web interface.
- Evaluate indexed vector search as the dataset grows.
