"""
ui.py
======
All Streamlit UI components for MetaAssist.
Kept separate from rag_pipeline.py so logic and interface never mix.

Author      : Kabilan TM
Internship  : Metaplore Solutions Pvt. Ltd.
"""

import streamlit as st


def apply_styles():
    """Inject custom CSS into the Streamlit app."""
    st.markdown("""
    <style>
        /* Header banner */
        .meta-header {
            background: linear-gradient(135deg, #1E2761 0%, #0D9488 100%);
            padding: 1.4rem 2rem;
            border-radius: 10px;
            margin-bottom: 1.2rem;
        }
        .meta-header h1 {
            color: white;
            margin: 0;
            font-size: 1.8rem;
            font-weight: 700;
        }
        .meta-header p {
            color: rgba(255,255,255,0.8);
            margin: 0.2rem 0 0;
            font-size: 0.9rem;
        }

        /* Chat bubbles */
        .bubble-user {
            background: #EEF2FF !important;
            border-radius: 10px 10px 2px 10px;
            padding: 0.7rem 1rem;
            margin: 0.4rem 0;
            border-left: 3px solid #6366F1;
            color: #1E1E2E !important;
        }
        .bubble-user * {
            color: #1E1E2E !important;
        }
        .bubble-bot {
            background: #F0FDF4 !important;
            border-radius: 10px 10px 10px 2px;
            padding: 0.7rem 1rem;
            margin: 0.4rem 0;
            border-left: 3px solid #0D9488;
            color: #1E1E2E !important;
        }
        .bubble-bot * {
            color: #1E1E2E !important;
        }
        .bubble-label {
            font-size: 0.75rem;
            font-weight: 600;
            margin-bottom: 0.3rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Source card */
        .source-card {
            background: #F8FAFC !important;
            border-left: 3px solid #0D9488;
            border-radius: 0 6px 6px 0;
            padding: 0.6rem 0.9rem;
            margin: 0.3rem 0;
            font-size: 0.83rem;
            color: #1E1E2E !important;
        }
        .source-card * {
            color: #1E1E2E !important;
        }

        /* Metric cards */
        .metric-row {
            display: flex;
            gap: 1rem;
            margin: 0.5rem 0;
        }

        /* Hide Streamlit default footer */
        footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render the top banner."""
    st.markdown("""
    <div class="meta-header">
        <h1>🤖 MetaAssist</h1>
        <p>Enterprise Document Intelligence Chatbot &nbsp;·&nbsp;
           Metaplore Solutions Pvt. Ltd. &nbsp;·&nbsp;
           Powered by Google Gemini + LangChain + FAISS</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar(rag_instance):
    """
    Render the sidebar with configuration controls, file uploader,
    and knowledge base stats.

    Returns:
        uploaded_files : list of uploaded file objects (may be empty)
        process_clicked: bool — True if the user clicked Process
        chunk_size     : int
        top_k          : int
    """
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")

        chunk_size = st.select_slider(
            "Chunk size (tokens)",
            options=[256, 512, 768, 1024],
            value=512,
            help="How many characters per text chunk. 512 is the optimal sweet spot."
        )

        top_k = st.slider(
            "Top-K retrieval",
            min_value=2, max_value=8, value=4,
            help="How many chunks to retrieve per question. More = broader context."
        )

        st.markdown("---")
        st.markdown("## 📂 Upload Documents")

        uploaded_files = st.file_uploader(
            "Upload PDF files (max 5)",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload the documents you want to query."
        )

        process_clicked = st.button(
            "🚀 Process Documents",
            use_container_width=True,
            type="primary"
        )

        # Knowledge base stats (shown only when docs are loaded)
        if st.session_state.get("docs_loaded"):
            st.markdown("---")
            st.markdown("## 📊 Knowledge Base")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Documents", len(st.session_state.doc_names))
            with col2:
                st.metric("Chunks", st.session_state.total_chunks)

            st.metric("Queries answered", st.session_state.query_count)

            st.markdown("**Loaded files:**")
            for name in st.session_state.doc_names:
                st.markdown(f"- 📄 `{name}`")

            st.markdown("---")
            if st.button("🗑️ Clear & Reset", use_container_width=True):
                # Reset all session state
                for key in ["rag", "chat_history", "docs_loaded",
                            "doc_names", "total_chunks", "query_count"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

        st.markdown("---")
        st.markdown(
            "<small style='color:#999'>Built by Kabilan TM<br>"
            "Metaplore Solutions · 2026</small>",
            unsafe_allow_html=True
        )

    return uploaded_files, process_clicked, chunk_size, top_k


def render_chat(chat_history):
    """Render the full conversation history as styled chat bubbles."""
    for turn in chat_history:
        # User bubble
        st.markdown(
            f'<div class="bubble-user">'
            f'<div class="bubble-label" style="color:#6366F1">You</div>'
            f'<span style="color:#1E1E2E">{turn["question"]}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Bot bubble
        st.markdown(
            f'<div class="bubble-bot">'
            f'<div class="bubble-label" style="color:#0D9488">MetaAssist</div>'
            f'<span style="color:#1E1E2E">{turn["answer"]}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Source citations (collapsible)
        if turn.get("sources"):
            with st.expander(
                f"📎 {len(turn['sources'])} source(s) used", expanded=False
            ):
                for i, src in enumerate(turn["sources"], 1):
                    st.markdown(
                        f'<div class="source-card">'
                        f'<b>#{i} &nbsp; 📄 {src["file"]} &nbsp;|&nbsp; '
                        f'Page {src["page"]}</b><br>'
                        f'<i>"{src["snippet"]}"</i>'
                        f'</div>',
                        unsafe_allow_html=True
                    )


def render_welcome():
    """Show a welcome message when no documents are loaded yet."""
    st.info("👈 Upload your PDF documents in the sidebar and click **Process Documents** to begin.")

    st.markdown("### What MetaAssist can do for you")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            "**🔍 Semantic Search**\n\n"
            "Finds answers by meaning — not just keyword matching."
        )
    with c2:
        st.markdown(
            "**📎 Source Citations**\n\n"
            "Every answer cites the exact document and page it came from."
        )
    with c3:
        st.markdown(
            "**💬 Conversation Memory**\n\n"
            "Ask follow-up questions — MetaAssist remembers context."
        )