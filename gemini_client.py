"""
utils/gemini_client.py
======================
PURPOSE:
  All communication with Google's Gemini API lives here.
  Mirrors the same method names as ai_client.py (Claude)
  so the TaskEngine works with BOTH without any changes.

HOW TO GET A FREE GEMINI KEY:
  1. Go to https://aistudio.google.com/app/apikey
  2. Click "Create API Key"
  3. Paste it in the sidebar under "Gemini API Key"
"""

import os
import re
import json


class GeminiClient:
    """
    Wraps the Google Gemini REST API.
    Uses gemini-2.0-flash — fast, free-tier friendly.

    Usage:
        client = GeminiClient()
        reply  = client.chat("Summarise this text: ...")
    """

    MODEL     = "gemini-2.0-flash"
    BASE_URL  = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "")

    # ── private helpers ───────────────────────────────────────────────

    def _call(self, system_prompt: str, user_message: str, max_tokens: int = 1500) -> str:
        """Send one request to Gemini, return the text reply."""
        import urllib.request
        if not self.api_key:
            raise ValueError(
                "Gemini API key not set. Please enter it in the sidebar."
            )

        url     = f"{self.BASE_URL}/{self.MODEL}:generateContent?key={self.api_key}"
        payload = json.dumps({
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_message}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7},
        }).encode()

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise ValueError(f"Gemini API error {e.code}: {body}") from e

    # ── public methods (same interface as AIClient) ───────────────────

    def chat(self, prompt: str) -> str:
        system = (
            "You are a helpful AI assistant that automates tasks efficiently. "
            "Always be concise, structured, and practical in your responses."
        )
        return self._call(system, prompt)

    def classify_task(self, task_description: str) -> dict:
        system = (
            "You are a task classifier. Analyse the user task and respond "
            "ONLY with a JSON object (no markdown fences) in this exact format:\n"
            '{"category": "<one of: text|data|web|email|code|general>", '
            '"complexity": "<low|medium|high>", '
            '"confidence": <0.0-1.0>, '
            '"estimated_time": "<e.g. 2 seconds>"}'
        )
        raw = self._call(system, task_description, max_tokens=200)
        try:
            clean = re.sub(r"```(?:json)?|```", "", raw).strip()
            return json.loads(clean)
        except Exception:
            return {"category": "general", "complexity": "medium",
                    "confidence": 0.7, "estimated_time": "3 seconds"}

    def summarise(self, text: str) -> str:
        system = (
            "You are an expert summariser. Create a clear, concise bullet-point "
            "summary that captures the key points of any text provided."
        )
        return self._call(system, f"Summarise the following:\n\n{text}")

    def translate(self, text: str, target_language: str) -> str:
        system = (
            f"You are a professional translator. Translate the given text into "
            f"{target_language}. Keep the tone and meaning intact."
        )
        return self._call(system, text)

    def generate_email(self, context: str) -> str:
        system = (
            "You are an expert business writer. Draft a professional, polished "
            "email based on the context. Include subject line, greeting, body, "
            "and sign-off."
        )
        return self._call(system, f"Write an email for this context:\n\n{context}", max_tokens=600)

    def analyse_sentiment(self, text: str) -> dict:
        system = (
            "You are a sentiment analysis engine. Analyse the sentiment and respond "
            "ONLY with a JSON object (no markdown):\n"
            '{"sentiment": "<Positive|Negative|Neutral|Mixed>", '
            '"score": <-1.0 to 1.0>, '
            '"emotion": "<e.g. happy, frustrated, neutral>", '
            '"explanation": "<one sentence>"}'
        )
        raw = self._call(system, text, max_tokens=300)
        try:
            clean = re.sub(r"```(?:json)?|```", "", raw).strip()
            return json.loads(clean)
        except Exception:
            return {"sentiment": "Neutral", "score": 0.0,
                    "emotion": "neutral", "explanation": "Could not analyse sentiment."}

    def generate_code(self, description: str, language: str = "Python") -> str:
        system = (
            f"You are a senior {language} developer. Write clean, well-commented, "
            f"production-ready {language} code with a brief explanation at the end."
        )
        return self._call(system, f"Write {language} code to: {description}", max_tokens=1200)

    def extract_keywords(self, text: str) -> list:
        system = (
            "Extract the most important keywords and topics from the given text. "
            "Return them as a JSON array of strings only (no markdown)."
        )
        raw = self._call(system, text, max_tokens=300)
        try:
            clean = re.sub(r"```(?:json)?|```", "", raw).strip()
            return json.loads(clean)
        except Exception:
            return ["keyword extraction failed"]

    def answer_question(self, question: str, context: str = "") -> str:
        system = (
            "You are a knowledgeable assistant. Answer questions accurately and "
            "concisely. If uncertain, say so clearly."
        )
        prompt = question if not context else f"Context:\n{context}\n\nQuestion: {question}"
        return self._call(system, prompt)

    def update_api_key(self, key: str):
        self.api_key = key
        os.environ["GEMINI_API_KEY"] = key
