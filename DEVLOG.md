# MetaAssist — Project Development Log

**Project:** Enterprise Document Intelligence Chatbot using RAG  
**Intern:** Kabilan TM  
**Organization:** Metaplore Solutions Pvt. Ltd.  
**Guide:** Mrs. Kalaiarasi – Tech Lead  
**Duration:** 02 February 2026 – 03 April 2026  
**Stack:** Python 3.12.6 · LangChain 1.2 · Google Gemini · FAISS · Streamlit  

---

## Session 1 — Project Setup & Environment (Apr 12, 2026)

### What was done
- Created GitHub repository: `metaassist` (public, Python .gitignore)
- Cloned repo locally to `C:\Users\kabil\metaassist`
- Created Python 3.12.6 virtual environment (`venv`)
- Installed all dependencies via `pip install -r requirements.txt`
- Created project folder structure:
  - `app/` — application logic
  - `app/utils/` — utility helpers (future use)
  - `app/rag_pipeline.py` — core RAG engine
  - `app/ui.py` — Streamlit UI components
  - `main.py` — entry point
  - `.env` — API keys (gitignored)
  - `DEVLOG.md` — this file
- Added `.env` and `venv/` to `.gitignore` to protect secrets
- Created Google Gemini API key (free tier, Default Gemini Project)
- First GitHub commit: `feat: initial project scaffold with RAG dependencies`

### Key decisions
- Used `venv` for isolation — keeps project dependencies clean
- Chose Google Gemini (free tier) over OpenAI to avoid costs
- Separated UI (`ui.py`) from logic (`rag_pipeline.py`) from the start —
  clean architecture makes future changes easier

### Dependencies installed
streamlit 1.56, langchain 1.2.15, langchain-community 0.4.1,
langchain-google-genai 4.2.1, faiss-cpu 1.13.2, pypdf 6.10,
google-generativeai 0.8.6, python-dotenv 1.2.2

---

## Session 2 — Core RAG Pipeline & UI Implementation (Apr 12, 2026)

### What was done
- Implemented `app/rag_pipeline.py` — the full RAG engine:
  - `_load_and_split()`: PyPDFLoader + RecursiveCharacterTextSplitter
    - Chunk size: 512 tokens, Overlap: 64 tokens
    - Hierarchical separators: paragraph → sentence → word → character
  - `_build_vector_store()`: Google embedding-001 (768-dim) + FAISS index
  - `query()`: semantic retrieval → prompt build → Gemini LLM → answer
  - `save_index()` / `load_index()`: FAISS index persistence
- Implemented `app/ui.py` — Streamlit UI components:
  - `apply_styles()`: custom CSS for chat bubbles, header, source cards
  - `render_header()`: branded top banner
  - `render_sidebar()`: file uploader, chunk/topK controls, stats panel
  - `render_chat()`: conversation history with source citation expanders
  - `render_welcome()`: onboarding screen for new sessions
- Implemented `main.py` — entry point:
  - Session state management for chat history, RAG instance, doc metadata
  - Temp file handling for uploaded PDFs
  - Full query → display → memory loop
- App tested locally with `streamlit run main.py`
- Second GitHub commit: `feat: implement core RAG pipeline, Streamlit UI, and main entry point`

### Architecture decisions
- `PromptTemplate` used over `ChatPromptTemplate` for simpler formatting
  with the newer LangChain 1.2 API
- Conversation history stored as `(user, assistant)` tuples — passed
  manually into prompt (last 5 turns) instead of using LangChain memory
  objects, which changed API in newer versions
- Source metadata formatted inline in context string with filename + page
  number so citations are natural in the LLM's answer
- UI and logic kept in completely separate files for clean separation of concerns

### RAG Pipeline — how it works
1. User uploads PDF(s) → saved to temp files
2. PyPDFLoader reads each PDF page by page
3. RecursiveCharacterTextSplitter divides text into 512-char chunks
   with 64-char overlap to preserve cross-boundary context
4. Google embedding-001 converts each chunk to a 768-dimensional vector
5. FAISS indexes all vectors for fast similarity search
6. User asks a question → question is embedded with same model
7. FAISS returns top-K most semantically similar chunks
8. Chunks + history + question injected into prompt template
9. Gemini 1.5 Flash generates a grounded, source-cited answer
10. Answer + source metadata displayed in Streamlit chat UI

---

## Next Steps
- [ ] Test with multiple PDFs simultaneously
- [ ] Add index save/load so documents don't need re-processing on refresh
- [ ] Add a typing animation while the bot is responding
- [ ] Improve source display with highlighted snippets
- [ ] Add export chat history as PDF feature

---

## Session 3 — Debugging API Compatibility & First Successful Query (Apr 12, 2026)

### What was done
- Debugged and resolved multiple API compatibility issues:

  1. **Embedding model 404** — `models/embedding-001` deprecated.
     Ran `check_models.py` diagnostic script using `genai.list_models()`
     to discover available models. Fixed to `models/gemini-embedding-001`.

  2. **LLM model 404** — `gemini-1.5-flash` not available on this API key.
     Listed generation models programmatically. Fixed to `gemini-2.0-flash`.

  3. **Gemini 429 quota error** — Free tier API quota is `limit: 0` for
     all Gemini generation models in India (regional restriction).
     Switched LLM from Google Gemini to **Groq** (free, globally available).
     - Model used: `llama-3.3-70b-versatile`
     - Embeddings remain on Google (`gemini-embedding-001`) — works fine.

  4. **langchain-core version conflict** — Multiple reinstall cycles to find
     compatible pinned versions. Final working set:
     - langchain==0.3.25
     - langchain-community==0.3.24
     - langchain-core==0.3.84
     - langchain-google-genai==2.0.7
     - langchain-groq==0.2.1
     - groq==0.9.0

  5. **httpx proxies error** — `groq 0.9.0` incompatible with `httpx 0.28.x`.
     Fixed by pinning `httpx==0.27.2`.

- **First successful end-to-end query** ✅
  - Uploaded resume PDF (KabilanTM.pdf)
  - Indexed 7 chunks successfully
  - Asked: "What is this document about?"
  - MetaAssist correctly identified: resume, name, degree, all 3 projects
  - Source citations displayed correctly with page and snippet

### Architecture — final working stack
| Component        | Technology                        |
|------------------|-----------------------------------|
| UI               | Streamlit 1.56                    |
| Embeddings       | Google gemini-embedding-001       |
| Vector Store     | FAISS                             |
| LLM              | Groq — llama-3.3-70b-versatile    |
| RAG Framework    | LangChain 0.3.25                  |
| PDF Parsing      | PyPDF + RecursiveTextSplitter     |

### Key lesson learned
- Google Gemini API free tier generation quota = 0 in India.
  Groq is the correct free alternative for Indian developers.
- Always pin dependency versions in requirements.txt for LangChain
  projects — the ecosystem moves fast and minor version mismatches
  break everything.
- Use `genai.list_models()` to programmatically discover available
  model names instead of assuming from documentation.

### GitHub commit
`feat: switch LLM to Groq (llama-3.3-70b) - fully working RAG pipeline`

---

## Next Steps (Session 4)
- [ ] Fix temp file name showing as `tmppow8lsxb.pdf` — show real filename
- [ ] Add index persistence (save/load FAISS index to avoid re-embedding)
- [ ] Add response time display in the chat
- [ ] Test with multiple PDFs simultaneously
- [ ] Improve UI — add typing indicator while generating
- [ ] Push all working code to GitHub