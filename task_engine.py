"""
utils/task_engine.py
====================
PURPOSE:
  The TaskEngine is the brain of the automation system.
  It decides WHAT to do with a user's request and then DOES it by
  calling the right method on AIClient.

HOW IT WORKS (for beginners):
  1. User types a task → TaskEngine.process(task)
  2. Engine classifies the task (text / data / code / email …)
  3. Engine runs the matching handler function
  4. Returns a structured TaskResult dict

DESIGN PATTERN USED: Strategy Pattern
  Each task type has its own handler function.  Adding a new task type
  is as simple as adding a new handler and registering it in HANDLERS.
"""

import time
import traceback
from dataclasses import dataclass, field
from typing import Any


# ─────────────────────────────────────────────────────────────────────
# DATA CLASSES  – lightweight containers for structured data
# ─────────────────────────────────────────────────────────────────────

@dataclass
class TaskResult:
    """Everything the UI needs to display the result of one task."""
    success: bool
    task_type: str
    input_text: str
    output: Any                    # str, dict, list – whatever makes sense
    category: str = "general"
    complexity: str = "medium"
    processing_time: float = 0.0
    confidence: float = 0.0
    error_message: str = ""
    metadata: dict = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────
# TASK ENGINE CLASS
# ─────────────────────────────────────────────────────────────────────

class TaskEngine:
    """
    Routes user requests to the correct AI handler and returns a TaskResult.

    Usage:
        engine = TaskEngine()
        result = engine.process(user_input, ai_client)
    """

    # Mapping: category → friendly display name
    CATEGORY_LABELS = {
        "text":    "Text Processing",
        "data":    "Data Analysis",
        "email":   "Email Generation",
        "code":    "Code Generation",
        "qa":      "Question Answering",
        "general": "General Task",
    }

    # ── public API ────────────────────────────────────────────────────

    def process(self, user_input: str, ai_client) -> TaskResult:
        """
        Main entry point.  Call this for every user request.

        Steps:
          1. Validate the input (not empty, not too long)
          2. Classify the task with AI
          3. Route to the correct handler
          4. Wrap everything in a TaskResult
        """
        start_time = time.time()

        # ── 1. Basic validation ──────────────────────────────────────
        validation_error = self._validate_input(user_input)
        if validation_error:
            return TaskResult(
                success=False,
                task_type="validation",
                input_text=user_input,
                output=None,
                error_message=validation_error,
            )

        # ── 2. Classify with AI ──────────────────────────────────────
        try:
            classification = ai_client.classify_task(user_input)
            category   = classification.get("category", "general")
            complexity = classification.get("complexity", "medium")
            confidence = classification.get("confidence", 0.7)
        except Exception as e:
            # If classification fails, fall back to general
            category, complexity, confidence = "general", "medium", 0.5

        # ── 3. Detect explicit overrides from keywords ───────────────
        category = self._keyword_override(user_input, category)

        # ── 4. Route to handler ──────────────────────────────────────
        try:
            handler   = self._get_handler(category)
            output    = handler(user_input, ai_client)
            elapsed   = round(time.time() - start_time, 2)

            return TaskResult(
                success=True,
                task_type=self.CATEGORY_LABELS.get(category, "General Task"),
                input_text=user_input,
                output=output,
                category=category,
                complexity=complexity,
                processing_time=elapsed,
                confidence=confidence,
                metadata={"classification": classification},
            )

        except ValueError as e:
            # Expected errors (e.g. missing API key)
            return TaskResult(
                success=False,
                task_type="error",
                input_text=user_input,
                output=None,
                error_message=str(e),
            )

        except Exception as e:
            # Unexpected errors – log full traceback for debugging
            return TaskResult(
                success=False,
                task_type="error",
                input_text=user_input,
                output=None,
                error_message=f"Unexpected error: {str(e)}",
                metadata={"traceback": traceback.format_exc()},
            )

    # ── private helpers ───────────────────────────────────────────────

    @staticmethod
    def _validate_input(text: str) -> str:
        """Return an error message string, or empty string if valid."""
        if not text or not text.strip():
            return "Task cannot be empty. Please describe what you want to automate."
        if len(text.strip()) < 5:
            return "Task is too short. Please provide more details."
        if len(text) > 5000:
            return "Task is too long (max 5 000 characters). Please shorten your request."
        return ""

    @staticmethod
    def _keyword_override(text: str, category: str) -> str:
        """
        Simple keyword-based override so the user can force a category.
        Example: "write an email to my manager…" → category = "email"
        """
        text_lower = text.lower()
        rules = {
            "email":   ["email", "mail", "write to", "message to"],
            "code":    ["code", "function", "script", "program", "class", "def "],
            "data":    ["analyse", "analyze", "data", "csv", "statistics", "chart"],
            "qa":      ["what is", "who is", "how does", "explain", "why", "when"],
            "text":    ["summarise", "summarize", "translate", "sentiment", "keywords"],
        }
        for cat, keywords in rules.items():
            if any(kw in text_lower for kw in keywords):
                return cat
        return category

    def _get_handler(self, category: str):
        """Return the handler function for the given category."""
        handlers = {
            "text":    self._handle_text,
            "data":    self._handle_data,
            "email":   self._handle_email,
            "code":    self._handle_code,
            "qa":      self._handle_qa,
            "general": self._handle_general,
        }
        return handlers.get(category, self._handle_general)

    # ── task handlers (one per category) ─────────────────────────────

    @staticmethod
    def _handle_text(task: str, ai: object) -> dict:
        """
        Text processing: summarise, translate, or sentiment analysis.
        Returns a dict so the UI can display each part separately.
        """
        task_lower = task.lower()
        result = {}

        if any(w in task_lower for w in ["summarise", "summarize", "summary"]):
            # Extract the text that appears after "summarise:" or similar
            text_to_process = task.split(":", 1)[-1].strip() if ":" in task else task
            result["type"]    = "Summary"
            result["summary"] = ai.summarise(text_to_process)

        elif any(w in task_lower for w in ["translate", "translation"]):
            # Try to detect target language ("translate to French: ...")
            import re
            lang_match = re.search(r"to\s+([A-Za-z]+)", task_lower)
            target_lang = lang_match.group(1).capitalize() if lang_match else "Spanish"
            text_part   = task.split(":", 1)[-1].strip() if ":" in task else task
            result["type"]       = "Translation"
            result["language"]   = target_lang
            result["translated"] = ai.translate(text_part, target_lang)

        elif any(w in task_lower for w in ["sentiment", "feeling", "emotion", "tone"]):
            text_part = task.split(":", 1)[-1].strip() if ":" in task else task
            result["type"]      = "Sentiment Analysis"
            result["analysis"]  = ai.analyse_sentiment(text_part)

        elif any(w in task_lower for w in ["keyword", "keywords", "topics", "extract"]):
            text_part = task.split(":", 1)[-1].strip() if ":" in task else task
            result["type"]     = "Keyword Extraction"
            result["keywords"] = ai.extract_keywords(text_part)

        else:
            # Fallback: general AI reply
            result["type"]   = "Text Processing"
            result["output"] = ai.chat(task)

        return result

    @staticmethod
    def _handle_data(task: str, ai: object) -> dict:
        """
        Data-related tasks: currently uses AI for analysis descriptions.
        Future: connect real CSV/DataFrame processing here.
        """
        response = ai.chat(
            f"You are a data analyst. The user wants you to help with: {task}\n\n"
            "Provide a detailed analysis plan, expected insights, and sample Python "
            "pandas/matplotlib code they could use."
        )
        return {"type": "Data Analysis", "output": response}

    @staticmethod
    def _handle_email(task: str, ai: object) -> str:
        """Generate a professional email draft."""
        return ai.generate_email(task)

    @staticmethod
    def _handle_code(task: str, ai: object) -> str:
        """Generate a code snippet from the description."""
        import re
        lang_match = re.search(r"\b(python|javascript|java|c\+\+|sql|bash|html)\b",
                               task.lower())
        language = lang_match.group(1).capitalize() if lang_match else "Python"
        return ai.generate_code(task, language)

    @staticmethod
    def _handle_qa(task: str, ai: object) -> str:
        """Answer a question."""
        return ai.answer_question(task)

    @staticmethod
    def _handle_general(task: str, ai: object) -> str:
        """Catch-all: send the task directly to the AI."""
        return ai.chat(task)
