"""
main.py
========
Entry point for MetaAssist.
Run with: streamlit run main.py

Author      : Kabilan TM
Internship  : Metaplore Solutions Pvt. Ltd.
"""

import os
import time
import json
import tempfile

import streamlit as st

from app.rag_pipeline import RAGPipeline
from app.ui import (
    apply_styles,
    render_header,
    render_sidebar,
    render_chat,
    render_welcome,
    render_load_previous,
)

INDEX_PATH = "faiss_index"
META_PATH  = os.path.join(INDEX_PATH, "session_meta.json")

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title = "MetaAssist | Document Intelligence",
    page_icon  = "🤖",
    layout     = "wide",
    initial_sidebar_state = "expanded"
)


# ── Session state initialisation ───────────────────────────────
def init_state():
    defaults = {
        "rag"          : None,
        "chat_history" : [],
        "conv_pairs"   : [],
        "docs_loaded"  : False,
        "doc_names"    : [],
        "total_chunks" : 0,
        "query_count"  : 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Helper: save session metadata ─────────────────────────────
def save_session_meta(doc_names, total_chunks):
    """Save doc names alongside the FAISS index for session restore."""
    os.makedirs(INDEX_PATH, exist_ok=True)
    with open(META_PATH, "w") as f:
        json.dump({"doc_names": doc_names, "total_chunks": total_chunks}, f)


def load_session_meta():
    """Load doc names from saved session metadata."""
    if os.path.exists(META_PATH):
        with open(META_PATH, "r") as f:
            return json.load(f)
    return {"doc_names": [], "total_chunks": 0}


# ── Apply styles & header ──────────────────────────────────────
apply_styles()
render_header()


# ── Sidebar ────────────────────────────────────────────────────
uploaded_files, process_clicked, chunk_size, top_k = render_sidebar(
    st.session_state.get("rag")
)

# ── Load previous session button ───────────────────────────────
load_previous = render_load_previous(INDEX_PATH)

if load_previous and not st.session_state.docs_loaded:
    with st.spinner("⚡ Loading previous session from disk..."):
        try:
            rag = RAGPipeline(chunk_size=chunk_size, top_k=top_k)
            meta = rag.load_index(INDEX_PATH)
            session = load_session_meta()

            st.session_state.rag          = rag
            st.session_state.docs_loaded  = True
            st.session_state.doc_names    = session.get("doc_names", ["Previously indexed docs"])
            st.session_state.total_chunks = session.get("total_chunks", meta.get("total_chunks", 0))
            st.session_state.chat_history = []
            st.session_state.conv_pairs   = []
            st.session_state.query_count  = 0

            st.success("✅ Previous session restored! Ready to answer questions.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Could not load previous session: {e}")


# ── Document processing ────────────────────────────────────────
if process_clicked:
    if not uploaded_files:
        st.warning("⚠️ Please upload at least one PDF before processing.")
    else:
        with st.spinner("📖 Reading and indexing your documents..."):
            try:
                tmp_paths = []
                doc_names = []

                for f in uploaded_files:
                    safe_name = f.name.replace(" ", "_")
                    tmp_path  = os.path.join(tempfile.gettempdir(), safe_name)
                    with open(tmp_path, "wb") as tmp:
                        tmp.write(f.read())
                    tmp_paths.append(tmp_path)
                    doc_names.append(f.name)

                rag = RAGPipeline(
                    chunk_size    = chunk_size,
                    chunk_overlap = 64,
                    top_k         = top_k
                )
                total_chunks = rag.load_documents(tmp_paths)

                # ── Auto-save index to disk ────────────────────
                rag.save_index(INDEX_PATH)
                save_session_meta(doc_names, total_chunks)

                st.session_state.rag          = rag
                st.session_state.docs_loaded  = True
                st.session_state.doc_names    = doc_names
                st.session_state.total_chunks = total_chunks
                st.session_state.chat_history = []
                st.session_state.conv_pairs   = []
                st.session_state.query_count  = 0

                st.success(
                    f"✅ {len(doc_names)} document(s) indexed — "
                    f"{total_chunks} chunks ready! "
                    f"💾 Index saved to disk."
                )
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error during processing: {e}")


# ── Main chat area ─────────────────────────────────────────────
if not st.session_state.docs_loaded:
    render_welcome()

else:
    render_chat(st.session_state.chat_history)

    if not st.session_state.chat_history:
        st.markdown("### 👋 Ready! Ask anything about your documents.")
        st.markdown(
            "**Try:** *What is this document about?* &nbsp;|&nbsp; "
            "*Summarize the key points* &nbsp;|&nbsp; "
            "*What does it say about [topic]?*"
        )

    st.markdown("---")

    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_query = st.text_input(
            "Your question",
            placeholder="Ask anything about your uploaded documents...",
            label_visibility="collapsed",
            key="query_input"
        )
    with col_btn:
        ask = st.button("Ask →", use_container_width=True, type="primary")

    if ask and user_query.strip():
        with st.spinner("🔍 Searching knowledge base..."):
            try:
                start  = time.time()
                result = st.session_state.rag.query(
                    question     = user_query,
                    chat_history = st.session_state.conv_pairs
                )
                elapsed = round(time.time() - start, 2)

                sources = []
                for doc in result["source_documents"]:
                    sources.append({
                        "file"   : os.path.basename(
                            doc.metadata.get("source", "Unknown")
                        ),
                        "page"   : doc.metadata.get("page", "N/A"),
                        "snippet": doc.page_content[:220].replace("\n", " ") + "..."
                    })

                st.session_state.chat_history.append({
                    "question": user_query,
                    "answer"  : result["answer"],
                    "sources" : sources,
                    "time"    : elapsed,
                })
                st.session_state.conv_pairs.append(
                    (user_query, result["answer"])
                )
                st.session_state.query_count += 1
                st.rerun()

            except Exception as e:
                st.error(f"❌ Query failed: {e}")