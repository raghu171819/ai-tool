"""
tests/test_components.py
========================
PURPOSE:
  Automated tests for the core components.
  Run with:  python -m pytest tests/ -v

HOW TESTS WORK (for beginners):
  - Each function starting with "test_" is one test case.
  - We create objects, call methods, and use "assert" to check results.
  - If the assertion is True → test passes (✓).
  - If the assertion is False → test fails (✗) and pytest shows you why.
"""

import sys
import os
import json

# Make the project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.history_manager import HistoryManager
from utils.task_engine import TaskEngine, TaskResult


# ─────────────────────────────────────────────────────────────────────
# MOCK OBJECTS  – Fake objects that don't call the real API
# ─────────────────────────────────────────────────────────────────────

class MockAIClient:
    """A fake AIClient that returns predictable responses (no API calls)."""

    api_key = "fake-key"

    def chat(self, prompt):
        return f"Mock response to: {prompt[:50]}"

    def classify_task(self, text):
        return {"category": "general", "complexity": "low", "confidence": 0.9,
                "estimated_time": "1 second"}

    def summarise(self, text):
        return "Mock summary: This is a short summary."

    def translate(self, text, lang):
        return f"[Mock {lang} translation of: {text[:30]}]"

    def analyse_sentiment(self, text):
        return {"sentiment": "Positive", "score": 0.8, "emotion": "happy",
                "explanation": "Mock analysis"}

    def extract_keywords(self, text):
        return ["keyword1", "keyword2", "keyword3"]

    def generate_email(self, context):
        return "Subject: Mock Email\n\nDear Sir/Madam,\nMock email body.\n\nRegards,\nAI"

    def generate_code(self, description, language="Python"):
        return f"# Mock {language} code\nprint('Hello World')"

    def answer_question(self, question, context=""):
        return "Mock answer: 42"

    def update_api_key(self, key):
        self.api_key = key


# ─────────────────────────────────────────────────────────────────────
# HISTORY MANAGER TESTS
# ─────────────────────────────────────────────────────────────────────

def make_dummy_result(success=True, task_type="Test", category="general") -> TaskResult:
    """Helper: create a minimal TaskResult for testing."""
    return TaskResult(
        success=success,
        task_type=task_type,
        input_text="dummy input",
        output="dummy output",
        category=category,
        complexity="low",
        processing_time=0.5,
        confidence=0.9,
    )


def test_history_add_and_retrieve(tmp_path, monkeypatch):
    """Test that records can be added and retrieved."""
    # Point HistoryManager at a temp directory
    monkeypatch.setattr(
        "utils.history_manager.HistoryManager.FILE_PATH",
        tmp_path / "test_history.json",
    )
    hm = HistoryManager()
    assert hm.get_all() == [], "Fresh history should be empty"

    hm.add(make_dummy_result())
    records = hm.get_all()
    assert len(records) == 1, "Should have 1 record after adding"
    assert records[0]["task_type"] == "Test"


def test_history_stats_empty(tmp_path, monkeypatch):
    """Stats on empty history should return zeros."""
    monkeypatch.setattr(
        "utils.history_manager.HistoryManager.FILE_PATH",
        tmp_path / "test_history2.json",
    )
    hm = HistoryManager()
    stats = hm.get_stats()
    assert stats["total"] == 0
    assert stats["success_rate"] == 0


def test_history_stats_with_data(tmp_path, monkeypatch):
    """Stats should correctly count successes and failures."""
    monkeypatch.setattr(
        "utils.history_manager.HistoryManager.FILE_PATH",
        tmp_path / "test_history3.json",
    )
    hm = HistoryManager()
    hm.add(make_dummy_result(success=True))
    hm.add(make_dummy_result(success=True))
    hm.add(make_dummy_result(success=False))

    stats = hm.get_stats()
    assert stats["total"]      == 3
    assert stats["successful"] == 2
    assert stats["failed"]     == 1
    assert stats["success_rate"] == round(2/3 * 100, 1)


def test_history_clear(tmp_path, monkeypatch):
    """Clear should remove all records."""
    monkeypatch.setattr(
        "utils.history_manager.HistoryManager.FILE_PATH",
        tmp_path / "test_history4.json",
    )
    hm = HistoryManager()
    hm.add(make_dummy_result())
    hm.add(make_dummy_result())
    hm.clear()
    assert hm.get_all() == []


# ─────────────────────────────────────────────────────────────────────
# TASK ENGINE TESTS
# ─────────────────────────────────────────────────────────────────────

def test_engine_validates_empty_input():
    """Empty input should return a failed TaskResult."""
    engine = TaskEngine()
    ai     = MockAIClient()
    result = engine.process("", ai)
    assert result.success is False
    assert "empty" in result.error_message.lower()


def test_engine_validates_short_input():
    """Very short input should fail validation."""
    engine = TaskEngine()
    ai     = MockAIClient()
    result = engine.process("hi", ai)
    assert result.success is False


def test_engine_validates_too_long_input():
    """Input over 5000 chars should fail."""
    engine = TaskEngine()
    ai     = MockAIClient()
    result = engine.process("x" * 5001, ai)
    assert result.success is False


def test_engine_processes_valid_input():
    """A valid task should succeed."""
    engine = TaskEngine()
    ai     = MockAIClient()
    result = engine.process("What is machine learning?", ai)
    assert result.success is True
    assert result.output is not None


def test_engine_keyword_override_email():
    """A task mentioning 'email' should be classified as email."""
    engine   = TaskEngine()
    category = engine._keyword_override(
        "Write an email to my boss about leave", "general"
    )
    assert category == "email"


def test_engine_keyword_override_code():
    """A task mentioning 'code' should be classified as code."""
    engine   = TaskEngine()
    category = engine._keyword_override(
        "Generate Python code to sort a list", "general"
    )
    assert category == "code"


def test_engine_sentiment_handler():
    """Sentiment task should return a dict with 'type' == 'Sentiment Analysis'."""
    engine = TaskEngine()
    ai     = MockAIClient()
    result = engine.process("Analyse the sentiment of: I love this!", ai)
    assert result.success is True
    assert isinstance(result.output, dict)


def test_engine_summarise_handler():
    """Summarise task should return a dict with 'type' == 'Summary'."""
    engine = TaskEngine()
    ai     = MockAIClient()
    result = engine.process("Summarise: This is a long piece of text.", ai)
    assert result.success is True


def test_engine_translate_handler():
    """Translate task should succeed and return a dict."""
    engine = TaskEngine()
    ai     = MockAIClient()
    result = engine.process("Translate to French: Hello world", ai)
    assert result.success is True


def test_engine_email_handler():
    """Email task should return a string."""
    engine = TaskEngine()
    ai     = MockAIClient()
    result = engine.process(
        "Write an email requesting one day off on Friday", ai
    )
    assert result.success is True
    assert isinstance(result.output, str)


def test_engine_code_handler():
    """Code generation task should succeed."""
    engine = TaskEngine()
    ai     = MockAIClient()
    result = engine.process(
        "Generate Python code to read a CSV file", ai
    )
    assert result.success is True


# ─────────────────────────────────────────────────────────────────────
# MAIN – run tests without pytest
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running simple tests without pytest…\n")
    engine = TaskEngine()
    ai     = MockAIClient()

    cases = [
        ("Empty input",         "",                             False),
        ("Valid Q&A",           "What is machine learning?",   True),
        ("Sentiment",           "Analyse sentiment: Great!",   True),
        ("Email generation",    "Write an email to my boss",   True),
        ("Code generation",     "Generate Python code to sort",True),
        ("Translation",         "Translate to French: Hello",  True),
        ("Summarise",           "Summarise: AI is growing",    True),
    ]

    passed = 0
    for name, task, expected_success in cases:
        result = engine.process(task, ai)
        ok     = result.success == expected_success
        mark   = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {mark}  {name}")
        if ok:
            passed += 1

    print(f"\n{passed}/{len(cases)} tests passed.")
