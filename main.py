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
import tempfile

import streamlit as st

from app.rag_pipeline import RAGPipeline
from app.ui import (
    apply_styles,
    render_header,
    render_sidebar,
    render_chat,
    render_welcome,
)

# ── Page config (must be first Streamlit call) ─────────────────────────────
st.set_page_config(
    page_title = "MetaAssist | Document Intelligence",
    page_icon  = "🤖",
    layout     = "wide",
    initial_sidebar_state = "expanded"
)


# ── Session state initialisation ───────────────────────────────────────────
def init_state():
    defaults = {
        "rag"          : None,
        "chat_history" : [],        # List of {question, answer, sources}
        "conv_pairs"   : [],        # List of (user_msg, ai_msg) for memory
        "docs_loaded"  : False,
        "doc_names"    : [],
        "total_chunks" : 0,
        "query_count"  : 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Apply styles & render header ───────────────────────────────────────────
apply_styles()
render_header()


# ── Sidebar ────────────────────────────────────────────────────────────────
uploaded_files, process_clicked, chunk_size, top_k = render_sidebar(
    st.session_state.get("rag")
)


# ── Document processing ────────────────────────────────────────────────────
if process_clicked:
    if not uploaded_files:
        st.warning("⚠️ Please upload at least one PDF before processing.")
    else:
        with st.spinner("📖 Reading and indexing your documents..."):
            try:
                # Save uploaded files to a temp directory
                tmp_paths  = []
                doc_names  = []

                for f in uploaded_files:
                    # Save with the real filename so citations show correctly
                    safe_name = f.name.replace(" ", "_")
                    tmp_path = os.path.join(tempfile.gettempdir(), safe_name)
                    with open(tmp_path, "wb") as tmp:
                        tmp.write(f.read())
                    tmp_paths.append(tmp_path)
                    doc_names.append(f.name)

                # Build the RAG pipeline
                rag = RAGPipeline(
                    chunk_size    = chunk_size,
                    chunk_overlap = 64,
                    top_k         = top_k
                )
                total_chunks = rag.load_documents(tmp_paths)

                # Store in session
                st.session_state.rag           = rag
                st.session_state.docs_loaded   = True
                st.session_state.doc_names     = doc_names
                st.session_state.total_chunks  = total_chunks
                st.session_state.chat_history  = []
                st.session_state.conv_pairs    = []
                st.session_state.query_count   = 0

                st.success(
                    f"✅ {len(doc_names)} document(s) indexed — "
                    f"{total_chunks} chunks ready!"
                )
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error during processing: {e}")


# ── Main area ──────────────────────────────────────────────────────────────
if not st.session_state.docs_loaded:
    render_welcome()

else:
    # Render conversation history
    render_chat(st.session_state.chat_history)

    if not st.session_state.chat_history:
        st.markdown("### 👋 Ready! Ask anything about your documents.")
        st.markdown(
            "**Try:** *What is this document about?* &nbsp;|&nbsp; "
            "*Summarize the key points* &nbsp;|&nbsp; "
            "*What does it say about [topic]?*"
        )

    st.markdown("---")

    # Query input row
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

    # Process query
    if ask and user_query.strip():
        with st.spinner("🔍 Searching knowledge base..."):
            try:
                start  = time.time()
                result = st.session_state.rag.query(
                    question     = user_query,
                    chat_history = st.session_state.conv_pairs
                )
                elapsed = round(time.time() - start, 2)

                # Extract source info for display
                sources = []
                for doc in result["source_documents"]:
                    sources.append({
                        "file"    : os.path.basename(
                            doc.metadata.get("source", "Unknown")
                        ),
                        "page"    : doc.metadata.get("page", "N/A"),
                        "snippet" : doc.page_content[:220].replace("\n", " ") + "..."
                    })

                # Save to session state
                st.session_state.chat_history.append({
                    "question" : user_query,
                    "answer"   : result["answer"],
                    "sources"  : sources,
                    "time"     : elapsed,
                })

                # Save conversation pair for memory
                st.session_state.conv_pairs.append(
                    (user_query, result["answer"])
                )

                st.session_state.query_count += 1
                st.rerun()

            except Exception as e:
                st.error(f"❌ Query failed: {e}")