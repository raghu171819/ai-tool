"""
ui_components.py
================
PURPOSE:
  All Streamlit rendering (HTML, widgets, charts) lives here.
  app.py stays clean by importing from this file.

WHY SEPARATE THE UI?
  Keeping business logic (task_engine.py) and display code (here) in
  different files is called "Separation of Concerns".  It makes
  debugging and extending much easier.
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────────────────────────────────

def inject_css():
    """Inject custom CSS to make the app look polished."""
    st.markdown(
        """
        <style>
        /* ── Google Font ── */
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

        /* ── Global ── */
        html, body, [class*="css"] {
            font-family: 'Space Grotesk', sans-serif;
        }

        /* ── Hide default Streamlit chrome ── */
        #MainMenu, footer, header { visibility: hidden; }

        /* ── Main background ── */
        .stApp {
            background: linear-gradient(135deg, #0d0d14 0%, #13131f 50%, #0d1117 100%);
            color: #e8e8f0;
        }

        /* ── Cards ── */
        .task-card {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(99,102,241,0.25);
            border-radius: 16px;
            padding: 24px;
            margin: 12px 0;
            backdrop-filter: blur(12px);
            transition: border-color 0.3s ease;
        }
        .task-card:hover { border-color: rgba(99,102,241,0.55); }

        /* ── Hero header ── */
        .hero-title {
            font-size: 2.8rem;
            font-weight: 700;
            background: linear-gradient(90deg, #818cf8, #34d399, #60a5fa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.2;
        }
        .hero-sub {
            color: #6b7280;
            font-size: 1.05rem;
            margin-top: 6px;
        }

        /* ── Metric boxes ── */
        .metric-box {
            background: rgba(99,102,241,0.10);
            border: 1px solid rgba(99,102,241,0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .metric-val { font-size: 2rem; font-weight: 700; color: #818cf8; }
        .metric-lbl { font-size: 0.8rem; color: #9ca3af; margin-top: 4px; }

        /* ── Status pills ── */
        .pill {
            display: inline-block;
            padding: 3px 12px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .pill-success { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.3); }
        .pill-error   { background: rgba(239,68,68,0.15);  color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
        .pill-info    { background: rgba(99,102,241,0.15); color: #818cf8; border: 1px solid rgba(99,102,241,0.3); }

        /* ── Output box ── */
        .output-box {
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.88rem;
            white-space: pre-wrap;
            word-break: break-word;
            color: #d1d5db;
            max-height: 500px;
            overflow-y: auto;
        }

        /* ── Task textarea ── */
        .stTextArea textarea {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(99,102,241,0.3) !important;
            border-radius: 12px !important;
            color: #e8e8f0 !important;
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 1rem !important;
        }
        .stTextArea textarea:focus {
            border-color: #818cf8 !important;
            box-shadow: 0 0 0 2px rgba(129,140,248,0.2) !important;
        }

        /* ── Buttons ── */
        .stButton > button {
            background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            padding: 0.55rem 1.8rem !important;
            transition: opacity 0.2s !important;
        }
        .stButton > button:hover { opacity: 0.85 !important; }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            background: rgba(13,13,20,0.95) !important;
            border-right: 1px solid rgba(99,102,241,0.15) !important;
        }

        /* ── Tab text ── */
        .stTabs [data-baseweb="tab"] { color: #9ca3af !important; }
        .stTabs [aria-selected="true"] { color: #818cf8 !important; }

        /* ── Spinner ── */
        .stSpinner > div { border-top-color: #818cf8 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────

def render_header():
    st.markdown(
        """
        <div style="padding: 2rem 0 1.5rem;">
            <div class="hero-title">⚡ Intelligent Task Automation</div>
            <div class="hero-sub">
                Describe any task in plain English — AI understands, processes, and delivers.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────

def render_sidebar(history_manager, ai_client=None, gemini_client=None):
    import os

    st.markdown("### ⚙️ Configuration")
    st.markdown("---")

    # ── Model selector ────────────────────────────────────────────────
    st.markdown("#### 🤖 Choose AI Model")
    model_choice = st.radio(
        label="AI Model",
        options=["Gemini", "Claude (Anthropic)"],
        index=0 if st.session_state.get("selected_model", "Gemini") == "Gemini" else 1,
        label_visibility="collapsed",
        horizontal=True,
    )
    st.session_state.selected_model = model_choice.split()[0]  # "Gemini" or "Claude"

    st.markdown("---")

    # ── Gemini API Key ────────────────────────────────────────────────
    st.markdown("#### 🔑 Gemini API Key")
    gemini_key = st.text_input(
        "Gemini Key",
        type="password",
        help="Get your free key at aistudio.google.com/app/apikey",
        placeholder="AIza...",
        label_visibility="collapsed",
    )
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        if gemini_client:
            gemini_client.update_api_key(gemini_key)
        st.success("✓ Gemini key saved", icon="✅")
    elif os.environ.get("GEMINI_API_KEY"):
        st.success("✓ Gemini key active", icon="✅")

    # ── Anthropic API Key ─────────────────────────────────────────────
    st.markdown("#### 🔑 Anthropic API Key")
    claude_key = st.text_input(
        "Claude Key",
        type="password",
        help="Get your key at console.anthropic.com",
        placeholder="sk-ant-...",
        label_visibility="collapsed",
    )
    if claude_key:
        os.environ["ANTHROPIC_API_KEY"] = claude_key
        if ai_client:
            ai_client.update_api_key(claude_key)
        st.success("✓ Claude key saved", icon="✅")

    # ── Active model badge ────────────────────────────────────────────
    model_name = st.session_state.get("selected_model", "Gemini")
    model_color = "#4ade80" if model_name == "Gemini" else "#818cf8"
    model_icon  = "🟢" if model_name == "Gemini" else "🟣"
    st.markdown(
        f'<div style="background:rgba(255,255,255,0.04);border:1px solid {model_color}40;'
        f'border-radius:8px;padding:8px 12px;font-size:12px;color:{model_color};margin-top:4px;">'
        f'{model_icon} Using: <strong>{model_name}</strong></div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### 📊 Quick Stats")

    stats = history_manager.get_stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tasks Run", stats["total"])
        st.metric("Success Rate", f"{stats['success_rate']}%")
    with col2:
        st.metric("Successful", stats["successful"])
        st.metric("Avg Time", f"{stats['avg_time']}s")

    st.markdown("---")
    st.markdown("### 🕒 Recent Tasks")
    recent = history_manager.get_recent(3)
    if recent:
        for r in recent:
            icon = "✅" if r["success"] else "❌"
            ts   = r["timestamp"][11:16]
            st.markdown(f"{icon} `{ts}` — {r['task_type']}")
    else:
        st.caption("No tasks yet.")

    st.markdown("---")
    if st.button("🗑️ Clear All History", use_container_width=True):
        history_manager.clear()
        st.rerun()

    st.markdown("---")
    st.caption("Intelligent Task Automation v2.0  \nGemini · Claude AI")


# ─────────────────────────────────────────────────────────────────────
# TAB 1 – TASK AUTOMATOR
# ─────────────────────────────────────────────────────────────────────

EXAMPLE_TASKS = [
    "Summarise: Artificial Intelligence is transforming industries worldwide. "
    "From healthcare to finance, AI helps automate repetitive tasks, analyse "
    "large datasets, and make accurate predictions.",

    "Write an email to my manager requesting a 2-day leave next Friday and Monday "
    "for a family function.",

    "Generate Python code to read a CSV file and plot a bar chart of sales by month.",

    "Analyse the sentiment of: The product quality is absolutely outstanding! "
    "Delivery was fast and the customer support team was incredibly helpful.",

    "Translate to French: Hello, how are you? I hope you are having a wonderful day.",

    "What is machine learning? Explain in simple terms for a beginner.",

    "Extract keywords from: Deep learning models, neural networks, natural language "
    "processing, and computer vision are core subfields of artificial intelligence.",
]


def render_task_tab(ai_client, task_engine, history_manager):
    col_main, col_side = st.columns([3, 1])

    with col_main:
        st.markdown('<div class="task-card">', unsafe_allow_html=True)
        st.markdown("#### 📝 Describe Your Task")

        task_input = st.text_area(
            label="task_input",
            label_visibility="collapsed",
            placeholder=(
                "Type anything…\n\n"
                "• Summarise: <paste your text here>\n"
                "• Write an email to…\n"
                "• Generate Python code to…\n"
                "• Translate to Spanish: …\n"
                "• What is machine learning?"
            ),
            height=160,
            key="task_input_area",
        )

        btn_col, info_col = st.columns([1, 3])
        with btn_col:
            run_clicked = st.button("⚡ Run Task", use_container_width=True)
        with info_col:
            st.markdown(
                '<div style="color:#6b7280;font-size:0.82rem;padding-top:10px;">'
                "Supports: text summarisation · translation · sentiment · "
                "email drafting · code generation · Q&amp;A · and more"
                "</div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # ── Process the task ─────────────────────────────────────────
        if run_clicked:
            if not task_input.strip():
                st.warning("Please enter a task first.")
            elif not ai_client.api_key:
                st.error("⚠️ Please enter your Anthropic API key in the sidebar.")
            else:
                with st.spinner("🤖 AI is processing your task…"):
                    result = task_engine.process(task_input, ai_client)
                    history_manager.add(result)
                    st.session_state.current_result = result
                st.rerun()

        # ── Display result ───────────────────────────────────────────
        if st.session_state.current_result:
            _render_result(st.session_state.current_result)

    with col_side:
        st.markdown("#### 💡 Try an Example")
        for i, example in enumerate(EXAMPLE_TASKS):
            label = example[:45] + "…"
            if st.button(label, key=f"ex_{i}", use_container_width=True):
                st.session_state.task_input_area = example
                st.rerun()


def _render_result(result):
    """Render the TaskResult object beautifully."""
    st.markdown("---")

    # ── Meta badges ──
    status_pill = (
        '<span class="pill pill-success">✓ Success</span>'
        if result.success
        else '<span class="pill pill-error">✗ Failed</span>'
    )
    complexity_colors = {"low": "#34d399", "medium": "#fbbf24", "high": "#f87171"}
    comp_color = complexity_colors.get(result.complexity, "#9ca3af")

    st.markdown(
        f"""
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px;align-items:center;">
            {status_pill}
            <span class="pill pill-info">🏷 {result.task_type}</span>
            <span class="pill" style="background:rgba(0,0,0,0.3);color:{comp_color};border:1px solid {comp_color}40;">
                Complexity: {result.complexity}
            </span>
            <span class="pill" style="background:rgba(0,0,0,0.3);color:#9ca3af;border:1px solid #ffffff15;">
                ⏱ {result.processing_time}s
            </span>
            <span class="pill" style="background:rgba(0,0,0,0.3);color:#9ca3af;border:1px solid #ffffff15;">
                Confidence: {int(result.confidence * 100)}%
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not result.success:
        st.error(f"**Error:** {result.error_message}")
        return

    # ── Output ───────────────────────────────────────────────────────
    output = result.output
    st.markdown("#### 📤 Output")

    if isinstance(output, dict):
        _render_dict_output(output)
    elif isinstance(output, list):
        st.markdown('<div class="output-box">', unsafe_allow_html=True)
        for item in output:
            st.markdown(f"• {item}")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Plain string output
        st.markdown(
            f'<div class="output-box">{_escape(str(output))}</div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇️ Download Output",
            data=str(output),
            file_name=f"ai_output_{datetime.now():%Y%m%d_%H%M%S}.txt",
            mime="text/plain",
        )


def _render_dict_output(output: dict):
    """Render structured dict outputs (sentiment, keywords, etc.)."""
    output_type = output.get("type", "")

    if output_type == "Sentiment Analysis":
        analysis = output.get("analysis", {})
        sentiment = analysis.get("sentiment", "N/A")
        score     = analysis.get("score", 0)
        emotion   = analysis.get("emotion", "")
        explain   = analysis.get("explanation", "")

        colour = {"Positive": "#34d399", "Negative": "#f87171",
                  "Neutral": "#9ca3af", "Mixed": "#fbbf24"}.get(sentiment, "#9ca3af")

        st.markdown(
            f"""
            <div class="task-card" style="border-color:{colour}40;">
                <div style="font-size:2rem;font-weight:700;color:{colour}">{sentiment}</div>
                <div style="color:#9ca3af;margin:6px 0;">Emotion: {emotion} &nbsp;|&nbsp; Score: {score:+.2f}</div>
                <div style="color:#d1d5db;">{explain}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Score bar
        pct = int((score + 1) / 2 * 100)
        st.progress(pct / 100, text=f"Sentiment score: {score:+.2f}")

    elif output_type == "Keyword Extraction":
        keywords = output.get("keywords", [])
        pills = "".join(
            f'<span class="pill pill-info" style="margin:3px;">{kw}</span>'
            for kw in keywords
        )
        st.markdown(
            f'<div style="padding:12px 0;">{pills}</div>',
            unsafe_allow_html=True,
        )

    elif output_type == "Summary":
        st.markdown(
            f'<div class="output-box">{_escape(output.get("summary",""))}</div>',
            unsafe_allow_html=True,
        )

    elif output_type == "Translation":
        st.markdown(f"**Target language:** {output.get('language','')}")
        st.markdown(
            f'<div class="output-box">{_escape(output.get("translated",""))}</div>',
            unsafe_allow_html=True,
        )

    else:
        # Generic dict: just render the "output" key or dump as JSON
        text = output.get("output", json.dumps(output, indent=2))
        st.markdown(
            f'<div class="output-box">{_escape(str(text))}</div>',
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────
# TAB 2 – ANALYTICS
# ─────────────────────────────────────────────────────────────────────

def render_analytics_tab(history_manager):
    st.markdown("### 📊 Task Analytics")
    stats = history_manager.get_stats()

    if stats["total"] == 0:
        st.info("No tasks run yet.  Go to the ⚡ Task Automator tab and run your first task!")
        return

    # ── Top KPI row ──────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    kpis = [
        (stats["total"],        "Total Tasks"),
        (stats["successful"],   "Successful"),
        (stats["failed"],       "Failed"),
        (f"{stats['success_rate']}%", "Success Rate"),
    ]
    for col, (val, lbl) in zip([c1, c2, c3, c4], kpis):
        with col:
            st.markdown(
                f'<div class="metric-box">'
                f'<div class="metric-val">{val}</div>'
                f'<div class="metric-lbl">{lbl}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ───────────────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### Tasks by Category")
        cat = stats["category_counts"]
        if cat:
            df_cat = pd.DataFrame(
                {"Category": list(cat.keys()), "Count": list(cat.values())}
            ).sort_values("Count", ascending=False)
            st.bar_chart(df_cat.set_index("Category"))
        else:
            st.caption("No data yet.")

    with chart_col2:
        st.markdown("#### Complexity Distribution")
        dist = history_manager.get_complexity_distribution()
        df_dist = pd.DataFrame(
            {"Complexity": list(dist.keys()), "Count": list(dist.values())}
        )
        st.bar_chart(df_dist.set_index("Complexity"))

    # ── Daily trend ──────────────────────────────────────────────────
    daily = stats["daily_counts"]
    if len(daily) > 1:
        st.markdown("#### Daily Task Volume")
        df_daily = pd.DataFrame(
            {"Date": list(daily.keys()), "Tasks": list(daily.values())}
        ).sort_values("Date")
        st.line_chart(df_daily.set_index("Date"))

    # ── Avg time ─────────────────────────────────────────────────────
    st.markdown(
        f'<div class="task-card" style="margin-top:12px;">'
        f'<strong>⏱ Average Processing Time:</strong> {stats["avg_time"]} seconds per task'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────
# TAB 3 – HISTORY
# ─────────────────────────────────────────────────────────────────────

def render_history_tab(history_manager):
    st.markdown("### 🕒 Task History")

    history = history_manager.get_all()
    if not history:
        st.info("No history yet. Run a task to see it appear here.")
        return

    # ── Search / filter ──────────────────────────────────────────────
    search = st.text_input("🔍 Filter by keyword", placeholder="e.g. email, sentiment…")

    if search:
        history = [
            r for r in history
            if search.lower() in r["input"].lower()
            or search.lower() in r["task_type"].lower()
        ]
        st.caption(f"{len(history)} result(s) found.")

    # ── Table ────────────────────────────────────────────────────────
    if history:
        df = pd.DataFrame(history)

        # Format display columns
        display_df = df[[
            "id", "timestamp", "task_type", "category",
            "complexity", "success", "processing_time",
        ]].copy()
        display_df["timestamp"] = display_df["timestamp"].str[:16].str.replace("T", " ")
        display_df["success"]   = display_df["success"].map({True: "✅", False: "❌"})
        display_df.columns = [
            "ID", "Time", "Type", "Category", "Complexity", "Status", "Time (s)"
        ]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )

        # ── Individual record viewer ──────────────────────────────────
        st.markdown("---")
        record_ids = [r["id"] for r in history]
        selected_id = st.selectbox("View full record:", options=record_ids)
        record = next((r for r in history if r["id"] == selected_id), None)
        if record:
            with st.expander("📋 Full Record Details", expanded=True):
                st.json(record)

        # ── Download ──────────────────────────────────────────────────
        csv_data = df.to_csv(index=False)
        st.download_button(
            "⬇️ Export History as CSV",
            data=csv_data,
            file_name=f"task_history_{datetime.now():%Y%m%d}.csv",
            mime="text/csv",
        )


# ─────────────────────────────────────────────────────────────────────
# TAB 4 – HELP
# ─────────────────────────────────────────────────────────────────────

def render_help_tab():
    st.markdown("### 📘 How to Use This App")

    with st.expander("🚀 Getting Started", expanded=True):
        st.markdown(
            """
1. **Get an API key** — Sign up free at [console.anthropic.com](https://console.anthropic.com)
2. **Enter the key** in the sidebar (it's stored only for this session)
3. **Type a task** in plain English in the Task Automator tab
4. **Click ⚡ Run Task** — results appear in seconds!
            """
        )

    with st.expander("📝 Supported Task Types"):
        tasks = {
            "Text Summarisation": "Summarise: <paste your text here>",
            "Language Translation": "Translate to Spanish: Hello, how are you?",
            "Sentiment Analysis": "Analyse the sentiment of: I love this product!",
            "Keyword Extraction": "Extract keywords from: <paste your article>",
            "Email Drafting": "Write an email to my professor requesting an extension…",
            "Code Generation": "Generate Python code to read a CSV and plot a graph",
            "Question Answering": "What is the difference between AI and ML?",
        }
        for task_type, example in tasks.items():
            st.markdown(f"**{task_type}**")
            st.code(example, language=None)
            st.markdown("")

    with st.expander("❓ Frequently Asked Questions"):
        faqs = [
            ("Is my API key stored anywhere?",
             "No. The key is only kept in your browser session and is never saved to disk."),
            ("How much does it cost?",
             "Anthropic charges per token (roughly per word). "
             "Typical tasks cost a fraction of a cent."),
            ("Can I use this offline?",
             "No — the app needs an internet connection to reach the Claude API."),
            ("How do I add new task types?",
             "Add a handler method in utils/task_engine.py and register it in the HANDLERS dict."),
        ]
        for q, a in faqs:
            st.markdown(f"**Q: {q}**")
            st.markdown(f"A: {a}")
            st.markdown("")

    with st.expander("⚙️ Technical Details"):
        st.markdown(
            """
| Component | Technology |
|-----------|------------|
| Frontend  | Python · Streamlit |
| AI Engine | Anthropic Claude (claude-sonnet-4) |
| Storage   | JSON flat-file database |
| Charts    | Streamlit native charts · Pandas |
| Packaging | pip / requirements.txt |
            """
        )


# ─────────────────────────────────────────────────────────────────────
# UTILITY
# ─────────────────────────────────────────────────────────────────────

def _escape(text: str) -> str:
    """Escape HTML special characters to prevent injection."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
