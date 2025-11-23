"""
Provider-agnostic LLM client used by flashcard and quiz generators.
"""

from __future__ import annotations

from typing import Optional


class LLMClient:
    """
    Thin abstraction over different LLM vendors (OpenAI, Gemini).
    """

    def __init__(
        self,
        provider: str,
        model: str,
        *,
        openai_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
    ) -> None:
        self.provider = (provider or "gemini").lower()
        self.model = model
        self._openai_api_key = openai_api_key
        self._gemini_api_key = gemini_api_key

        self._openai_client = None
        self._gemini_model = None

    def generate_text(
        self,
        prompt: str,
        *,
        max_tokens: int,
        temperature: float = 0.7,
        model: Optional[str] = None,
    ) -> str:
        """
        Generate text from the configured provider.
        """
        target_model = model or self.model

        if self.provider == "openai":
            return self._generate_openai(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                model=target_model,
            )
        elif self.provider == "gemini":
            return self._generate_gemini(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                model=target_model,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    # ------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------
    def _ensure_openai_client(self):
        if self._openai_client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise ImportError(
                    "openai package not installed. Please run `pip install openai`."
                ) from exc

            if not self._openai_api_key:
                raise ValueError("OPENAI_API_KEY is not configured.")

            self._openai_client = OpenAI(api_key=self._openai_api_key)
        return self._openai_client

    def _generate_openai(
        self,
        prompt: str,
        *,
        max_tokens: int,
        temperature: float,
        model: str,
    ) -> str:
        client = self._ensure_openai_client()
        # Use the Responses API for modern models like gpt-5.1
        response = client.responses.create(
            model=model,
            input=prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        # Prefer the convenience helper when available
        text = getattr(response, "output_text", None)
        if text:
            return text.strip()

        # Fallback: manually aggregate text chunks
        chunks = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text_value = getattr(content, "text", None)
                if text_value:
                    chunks.append(text_value)
        return "".join(chunks).strip()

    # ------------------------------------------------------------------
    # Gemini
    # ------------------------------------------------------------------
    def _ensure_gemini_model(self, model: str):
        if self._gemini_model is None or getattr(self._gemini_model, "_model_name", None) != model:
            try:
                import google.generativeai as genai
            except ImportError as exc:
                raise ImportError(
                    "google-generativeai package not installed. Please run `pip install google-generativeai`."
                ) from exc

            if not self._gemini_api_key:
                raise ValueError("GEMINI_API_KEY is not configured.")

            genai.configure(api_key=self._gemini_api_key)
            self._gemini_model = genai.GenerativeModel(model)
            self._gemini_model._model_name = model  # type: ignore[attr-defined]
        return self._gemini_model

    def _generate_gemini(
        self,
        prompt: str,
        *,
        max_tokens: int,
        temperature: float,
        model: str,
    ) -> str:
        gemini_model = self._ensure_gemini_model(model)
        response = gemini_model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        text = getattr(response, "text", "") or ""
        return text.strip()

