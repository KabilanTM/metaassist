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
            "Chunk size (characters)",
            options=[256, 512, 768, 1024],
            value=512,
            help="How many characters per text chunk. Larger = more context per chunk but less precise retrieval. 512 is the optimal sweet spot."
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
                st.metric("Chunks indexed", st.session_state.total_chunks)

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

        # Bot bubble — check if it's a guardrail response
        time_str = f"&nbsp;·&nbsp;⏱ {turn['time']}s" if turn.get("time") else ""
        is_guardrail = "not available in the uploaded documents" in turn["answer"].lower()

        if is_guardrail:
            st.markdown(
                f'<div style="background:#FFF8E1;border-left:3px solid #F59E0B;'
                f'border-radius:10px 10px 10px 2px;padding:0.7rem 1rem;margin:0.4rem 0;">'
                f'<div style="font-size:0.75rem;font-weight:600;color:#B45309;'
                f'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.3rem;">'
                f'⚠️ MetaAssist{time_str}</div>'
                f'<span style="color:#78350F">{turn["answer"]}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="bubble-bot">'
                f'<div class="bubble-label" style="color:#0D9488">'
                f'MetaAssist<span style="color:#94A3B8;font-weight:400;'
                f'text-transform:none;letter-spacing:0">{time_str}</span>'
                f'</div>'
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
                        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
                        f'<span style="background:#0D9488;color:white;font-size:10px;'
                        f'font-weight:700;padding:2px 7px;border-radius:10px;">#{i}</span>'
                        f'<span style="font-weight:600;color:#1E293B;font-size:0.85rem;">'
                        f'📄 {src["file"]}</span>'
                        f'<span style="color:#94A3B8;font-size:0.8rem;">Page {src["page"]}</span>'
                        f'</div>'
                        f'<div style="background:#F1F5F9;border-radius:6px;padding:6px 10px;'
                        f'font-size:0.82rem;color:#334155;line-height:1.5;">'
                        f'<span style="color:#0D9488;font-weight:600;">Retrieved passage:</span> '
                        f'{src["snippet"]}'
                        f'</div>'
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

def render_load_previous(index_path: str = "faiss_index") -> bool:
    """
    Show a 'Load Previous Session' button if a saved index exists.
    Returns True if the user clicked the load button.
    """
    import os
    if os.path.exists(os.path.join(index_path, "index.faiss")):
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 💾 Previous Session")
        st.sidebar.info("A saved knowledge base was found from your last session.")
        return st.sidebar.button(
            "⚡ Load Previous Session",
            use_container_width=True,
            help="Reload the last indexed documents without re-uploading"
        )
    return False

def render_export_button(chat_history: list):
    """
    Render a Download Chat button if there is conversation history.
    Exports the full conversation as a formatted .txt file.
    """
    if not chat_history:
        return

    lines = []
    lines.append("=" * 60)
    lines.append("MetaAssist — Conversation Export")
    lines.append("Metaplore Solutions Pvt. Ltd.")
    lines.append("=" * 60)
    lines.append("")

    for i, turn in enumerate(chat_history, 1):
        lines.append(f"[{i}] YOU:")
        lines.append(f"    {turn['question']}")
        lines.append("")
        lines.append(f"    METAASSIST ({turn.get('time', '?')}s):")
        # Word-wrap the answer at 70 chars
        answer = turn["answer"]
        words, line_buf = answer.split(), []
        char_count = 0
        for word in words:
            if char_count + len(word) + 1 > 70:
                lines.append(f"    {'  '.join(line_buf)}")
                line_buf, char_count = [word], len(word)
            else:
                line_buf.append(word)
                char_count += len(word) + 1
        if line_buf:
            lines.append(f"    {' '.join(line_buf)}")
        lines.append("")
        if turn.get("sources"):
            lines.append("    Sources:")
            for src in turn["sources"]:
                lines.append(f"      • {src['file']} | Page {src['page']}")
        lines.append("-" * 60)
        lines.append("")

    export_text = "\n".join(lines)

    st.download_button(
        label      = "💾 Export Chat (.txt)",
        data       = export_text,
        file_name  = "metaassist_conversation.txt",
        mime       = "text/plain",
        use_container_width = True,
    )