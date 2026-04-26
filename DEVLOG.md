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

---

## Session 4 — Priority 1 Improvements (Apr 23, 2026)

### What was done

**Fix 1 — Characters vs Tokens terminology correction**
- The sidebar label said "Chunk size (tokens)" which was technically wrong.
  `RecursiveCharacterTextSplitter` uses character count, not token count.
- Fixed label to "Chunk size (characters)" in `app/ui.py`
- Updated help text to explain the trade-off clearly
- Lesson: code and documentation must match exactly — an interviewer or
  professor will catch this kind of inconsistency

**Fix 2 — Response time display in chat bubbles**
- Added elapsed time (e.g. "⏱ 2.94s") next to the MetaAssist label
  in every bot response bubble
- Implemented by recording `time.time()` before and after `rag.query()`
  in `main.py` and storing it in the chat history dict
- Displayed inline in `render_chat()` in `app/ui.py` using a styled span
- This makes the app feel production-grade and gives real data for the
  evaluation/experiments section of the presentation

**Feature 3 — FAISS Index Persistence (save/load)**
- Problem before: every time the app restarted or the page refreshed,
  users had to re-upload and re-embed all documents. For large corpora
  this could take 30–60 seconds.
- Solution: automatically save the FAISS index to disk after processing
  using `vector_store.save_local("faiss_index/")` and restore it on
  next launch with `vector_store.load_local()`
- Also saves a `session_meta.json` alongside the index storing:
  doc_names and total_chunks so the sidebar stats restore correctly
- Added `render_load_previous()` in `ui.py` — shows a "⚡ Load Previous
  Session" button in the sidebar whenever a saved index is detected
- Added `RAGPipeline.index_exists()` static method for clean existence check
- Updated `main.py` to auto-save after every successful processing run
  and handle load-previous button click with full session state restore

### Test results
- Indexed STATEMENT_OF_PURPOSE.pdf → 6 chunks → index saved to disk
- Stopped app, restarted → "Load Previous Session" button appeared
- Clicked load → index restored instantly, no re-upload needed
- Asked "What is this document about?" → correct answer in 2.94s
- Response time displayed correctly in chat bubble

### Files changed
- `app/rag_pipeline.py` — updated save_index(), load_index(), added index_exists()
- `app/ui.py` — fixed chunk size label, added time display, added render_load_previous()
- `main.py` — complete rewrite with auto-save, load-previous flow, session meta

### GitHub commit
`feat: index persistence, response time display, fix characters vs tokens wording`

---

## Next Steps (Session 5 — Priority 2)
- [ ] Document summarization button per uploaded PDF
- [ ] Source highlighting — bold the key snippet in citation cards
- [ ] Chat export — download conversation as .txt file
- [ ] Guardrail visibility — distinct UI card when answer not found in docs

---

## Session 4 — Priority 1 Improvements (Apr 23, 2026)

### What was done

**Fix 1 — Terminology correction (characters vs tokens)**
- The sidebar label said "Chunk size (tokens)" but the code uses
  `RecursiveCharacterTextSplitter` which splits on character count, not tokens.
- Fixed label to "Chunk size (characters)" in `app/ui.py`.
- Also updated the help tooltip to explain the trade-off clearly.
- This matters because an interviewer or professor would catch this mismatch
  immediately if the code and UI don't agree.

**Fix 2 — Response time display**
- Added elapsed time display to every MetaAssist chat bubble.
- Format: "METAASSIST · ⏱ 2.94s"
- Implementation: `time.time()` before and after `rag.query()` in `main.py`,
  stored in session state with each chat turn, rendered in `render_chat()`
  in `ui.py`.
- Observed response times: 2–4 seconds on Groq free tier with 512-char chunks.

**Fix 3 — FAISS Index Persistence (major feature)**
- Problem: every page refresh required re-uploading and re-embedding documents.
  For large documents this takes 10–30 seconds and wastes API calls.
- Solution: auto-save the FAISS index to disk after every successful ingestion.

- How it works:
  1. After `load_documents()` succeeds, `rag.save_index("faiss_index/")` is
     called automatically in `main.py`.
  2. A companion `session_meta.json` file is saved alongside the index,
     storing doc names and chunk count so the UI can restore sidebar stats.
  3. On next launch, `render_load_previous()` in `ui.py` detects the saved
     index and shows a "⚡ Load Previous Session" button in the sidebar.
  4. Clicking it calls `rag.load_index()` which deserializes the FAISS index
     from disk and rebuilds the retriever — no re-embedding required.

- Files saved to faiss_index/ folder:
    - index.faiss   → the actual FAISS vector index
    - index.pkl     → chunk metadata (source, page numbers)
    - meta.json     → pipeline config (chunk_size, top_k, total_chunks)
    - session_meta.json → doc names for UI display

- The faiss_index/ folder is listed in .gitignore so it is never committed.

- Test result: uploaded STATEMENT_OF_PURPOSE.pdf, indexed 6 chunks, stopped
  the app, restarted, clicked "Load Previous Session" — app answered correctly
  without any re-upload. ✅

### Files changed
- `app/rag_pipeline.py` — updated save_index(), load_index(), added index_exists()
- `app/ui.py` — fixed label, added time display in render_chat(), added render_load_previous()
- `main.py` — full rewrite with auto-save after processing, load previous session flow

### GitHub commit
`feat: index persistence with save/load, response time display, fix characters vs tokens label`

### Performance observation
- First run (with embedding): ~15–20 seconds for a 6-chunk document
- Subsequent runs (load from disk): ~1–2 seconds
- This is a 10x speedup and a strong talking point for the presentation

---

## Next Steps (Session 5 — Priority 2)
- [ ] Document summarization button ("📋 Summarize this PDF")
- [ ] Source highlighting — bold the key phrase in citation snippets
- [ ] Chat export — download full conversation as .txt file
- [ ] Guardrail visibility — distinct UI card for "not found in documents"