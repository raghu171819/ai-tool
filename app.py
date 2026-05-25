"""
============================================================
  Intelligent Task Automation using AI
  Main Application Entry Point  (v2 — Claude + Gemini)
============================================================
"""

import streamlit as st
from utils.task_engine import TaskEngine
from utils.history_manager import HistoryManager
from utils.ai_client import AIClient
from utils.gemini_client import GeminiClient
import ui_components as ui

st.set_page_config(
    page_title="AI Task Automator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

ui.inject_css()

# ── session state ─────────────────────────────────────────────────────
if "history_manager" not in st.session_state:
    st.session_state.history_manager = HistoryManager()
if "task_engine" not in st.session_state:
    st.session_state.task_engine = TaskEngine()
if "ai_client" not in st.session_state:
    st.session_state.ai_client = AIClient()
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = GeminiClient()
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "Gemini"   # default

# ── sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    ui.render_sidebar(
        st.session_state.history_manager,
        st.session_state.ai_client,
        st.session_state.gemini_client,
    )

# ── header ────────────────────────────────────────────────────────────
ui.render_header()

# ── tabs ──────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "⚡ Task Automator",
    "📊 Analytics",
    "🕒 History",
    "📘 Help",
])

# Pick the active client based on sidebar selection
active_client = (
    st.session_state.gemini_client
    if st.session_state.selected_model == "Gemini"
    else st.session_state.ai_client
)

with tab1:
    ui.render_task_tab(
        active_client,
        st.session_state.task_engine,
        st.session_state.history_manager,
    )
with tab2:
    ui.render_analytics_tab(st.session_state.history_manager)
with tab3:
    ui.render_history_tab(st.session_state.history_manager)
with tab4:
    ui.render_help_tab()
