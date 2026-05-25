"""
utils/ai_client.py
==================
PURPOSE:
  All communication with the Anthropic Claude API lives here.
  The rest of the app just calls ai_client.chat(prompt) or
  ai_client.classify_task(text) and gets clean results back.

KEY IDEA FOR BEGINNERS:
  An API (Application Programming Interface) is like a waiter at a
  restaurant.  You tell the waiter what you want (prompt), the kitchen
  (Claude) prepares it, and the waiter brings back the result.
"""

import os
import re
import anthropic
import streamlit as st


class AIClient:
    """
    Wraps the Anthropic Python SDK.
    
    Usage:
        client = AIClient()
        reply  = client.chat("Summarise this text: ...")
    """

    # The model we want to use (Claude Sonnet is fast and smart)
    MODEL = "claude-sonnet-4-20250514"

    def __init__(self):
        # Grab the API key that the user entered in the sidebar.
        # os.environ is a dictionary of environment variables.
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self._client = None  # Lazy-initialised below

    # ── private helpers ───────────────────────────────────────────────

    def _get_client(self):
        """Return a cached Anthropic client, or raise a friendly error."""
        if not self.api_key:
            raise ValueError(
                "API key not set. Please enter your Anthropic API key in the sidebar."
            )
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def _call(self, system_prompt: str, user_message: str, max_tokens: int = 1500) -> str:
        """
        Low-level helper: send one message, return the text reply.
        
        Args:
            system_prompt : Instructions that define the AI's role/behaviour.
            user_message  : The actual request from the user.
            max_tokens    : Maximum length of the AI's response.
        """
        client = self._get_client()
        message = client.messages.create(
            model=self.MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        # message.content is a list of blocks; we only need the text.
        return message.content[0].text

    # ── public methods ────────────────────────────────────────────────

    def chat(self, prompt: str) -> str:
        """General-purpose chat – returns the AI's plain-text reply."""
        system = (
            "You are a helpful AI assistant that automates tasks efficiently. "
            "Always be concise, structured, and practical in your responses."
        )
        return self._call(system, prompt)

    def classify_task(self, task_description: str) -> dict:
        """
        Asks Claude to classify the task into a category and estimate
        complexity.  Returns a dict like:
            { "category": "text", "complexity": "low", "confidence": 0.95 }
        """
        system = (
            "You are a task classifier. Analyse the user's task and respond "
            "ONLY with a JSON object (no markdown fences) in this exact format:\n"
            '{"category": "<one of: text|data|web|email|code|general>", '
            '"complexity": "<low|medium|high>", '
            '"confidence": <0.0-1.0>, '
            '"estimated_time": "<e.g. 2 seconds>"}'
        )
        raw = self._call(system, task_description, max_tokens=200)
        try:
            import json
            # Strip any accidental markdown fences
            clean = re.sub(r"```(?:json)?|```", "", raw).strip()
            return json.loads(clean)
        except Exception:
            # Safe fallback if the model doesn't return valid JSON
            return {
                "category": "general",
                "complexity": "medium",
                "confidence": 0.7,
                "estimated_time": "3 seconds",
            }

    def summarise(self, text: str) -> str:
        """Return a bullet-point summary of the given text."""
        system = (
            "You are an expert summariser. Create a clear, concise bullet-point "
            "summary that captures the key points of any text provided."
        )
        return self._call(system, f"Summarise the following:\n\n{text}")

    def translate(self, text: str, target_language: str) -> str:
        """Translate text into the target language."""
        system = (
            f"You are a professional translator. Translate the given text into "
            f"{target_language}. Keep the tone and meaning intact."
        )
        return self._call(system, text)

    def generate_email(self, context: str) -> str:
        """Draft a professional email based on the context description."""
        system = (
            "You are an expert business writer. Draft a professional, polished "
            "email based on the context. Include subject line, greeting, body, "
            "and sign-off. Use clear, friendly yet formal language."
        )
        return self._call(system, f"Write an email for this context:\n\n{context}", max_tokens=600)

    def analyse_sentiment(self, text: str) -> dict:
        """
        Perform sentiment analysis on the text.
        Returns { "sentiment": "...", "score": ..., "explanation": "..." }
        """
        system = (
            "You are a sentiment analysis engine. Analyse the sentiment of the "
            "given text and respond ONLY with a JSON object (no markdown):\n"
            '{"sentiment": "<Positive|Negative|Neutral|Mixed>", '
            '"score": <-1.0 to 1.0>, '
            '"emotion": "<e.g. happy, frustrated, neutral>", '
            '"explanation": "<one sentence>"}'
        )
        raw = self._call(system, text, max_tokens=300)
        try:
            import json
            clean = re.sub(r"```(?:json)?|```", "", raw).strip()
            return json.loads(clean)
        except Exception:
            return {
                "sentiment": "Neutral",
                "score": 0.0,
                "emotion": "neutral",
                "explanation": "Could not analyse sentiment.",
            }

    def generate_code(self, description: str, language: str = "Python") -> str:
        """Generate a code snippet from a plain-English description."""
        system = (
            f"You are a senior {language} developer. Write clean, well-commented, "
            f"production-ready {language} code. Include a brief explanation of how "
            f"the code works at the end."
        )
        return self._call(
            system,
            f"Write {language} code to: {description}",
            max_tokens=1200,
        )

    def extract_keywords(self, text: str) -> list:
        """Return a list of keywords/topics from the text."""
        system = (
            "Extract the most important keywords and topics from the given text. "
            "Return them as a JSON array of strings only (no markdown)."
        )
        raw = self._call(system, text, max_tokens=300)
        try:
            import json
            clean = re.sub(r"```(?:json)?|```", "", raw).strip()
            return json.loads(clean)
        except Exception:
            return ["keyword extraction failed"]

    def answer_question(self, question: str, context: str = "") -> str:
        """Answer a question, optionally using provided context."""
        system = (
            "You are a knowledgeable assistant. Answer questions accurately and "
            "concisely. If context is provided, base your answer on it. If you're "
            "uncertain, say so clearly."
        )
        prompt = question if not context else f"Context:\n{context}\n\nQuestion: {question}"
        return self._call(system, prompt)

    def update_api_key(self, key: str):
        """Allow the user to update the API key at runtime."""
        self.api_key = key
        self._client = None  # Force re-initialisation with new key
        os.environ["ANTHROPIC_API_KEY"] = key
