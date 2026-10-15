# Software Support RAG Assistant

A small learning project that explores retrieval-augmented generation (RAG)
for software troubleshooting using simulated documentation and the Gemini API.

The project focuses on understanding the full workflow, evaluating answer
quality, and gradually improving retrieval and system integration.

## Current Features

- Load a local Markdown knowledge document.
- Split the document into sections using headings.
- Retrieve troubleshooting sections by an exact error code.
- Include the document ID and filename as source information.
- Generate Traditional Chinese answers using Gemini.
- Measure the total API response time.

## How It Works

1. The user enters an error code, such as `E202`.
2. The programme retrieves the matching section from the document.
3. The retrieved content and source information are added to a prompt.
4. Gemini generates an answer based on the supplied reference material.

Currently, retrieval uses exact error-code matching rather than vector search.
The question sent to the model is a predefined test question.

## Tech Stack

- Python 3.11
- Google GenAI SDK
- Gemini API
- Markdown documents
- Git and GitHub

## Getting Started

The commands below are for Windows PowerShell.

### 1. Clone the repository

```powershell
git clone https://github.com/WenHsi08/software-support-rag.git
cd software-support-rag
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

### 4. Set your API key

Create your own Gemini API key in Google AI Studio, then set it in the current terminal:

```powershell
$env:GEMINI_API_KEY = "YOUR_API_KEY"
```

Do not commit API keys to the repository.
This environment variable must be set again when opening a new terminal.

### 5. Run the assistant

```powershell
python read_docs.py
```

Enter `E201` or `E202` to retrieve the corresponding troubleshooting section
and generate an answer. An unknown code such as `E999` returns a local
“no matching documentation” message without calling the model.

The current model is `gemini-3.8-flash`. Model availability and API quotas
depend on the provider and account.

## Project Files

| File | Purpose |
| --- | --- |
| `read_docs.py` | Document loading, retrieval, prompt construction and answer generation |
| `check_models.py` | List models that support content generation |
| `test_llm.py` | Manually check a basic LLM API call |
| `docs/report_export.md` | Simulated report-export troubleshooting document |

## Current Limitations

- The knowledge base contains one simulated document covering two error codes.
- Users cannot yet enter a full natural-language question.
- There is no vector search, conversation history or web interface.
- API failures are not yet handled gracefully.
- Answers may still contain unsupported assumptions and require evaluation.
- The assistant does not create tickets, report issues or change permissions.
- Automated tests have not yet been added.

## Planned Improvements

- Support user-written questions.
- Expand the simulated knowledge base.
- Add semantic retrieval and compare it with exact code matching.
- Evaluate answer accuracy, source attribution and handling of missing information.
- Add error handling and automated tests.
- Build a FastAPI backend and a web interface.
- Explore a desktop companion interface as an optional extension.