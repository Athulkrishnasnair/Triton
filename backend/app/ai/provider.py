"""Pluggable language model boundary and optional Gemini implementation."""

import json
import os
from typing import Protocol, runtime_checkable


@runtime_checkable
class AIProvider(Protocol):
    """An AI provider explains backend supplied facts; it does not source them."""

    def explain(self, question: str, structured_context: dict) -> str:
        """Explain verified context in natural language.

        TODO: add a Gemini adapter (or another provider) when the assistant is
        implemented. Never let the model invent live harbour facts.
        """
        ...


class GeminiProvider:
    """Gemini adapter that only explains structured backend supplied facts."""

    def explain(self, question: str, structured_context: dict) -> str:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("Gemini is not configured.")
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=10000),
            )
            model = os.environ.get("GEMINI_MODEL", "").strip() or "gemini-2.0-flash"
            response = client.models.generate_content(
                model=model,
                contents=(
                    f"User question:\n{question}\n\n"
                    "Verified structured context JSON:\n"
                    f"{json.dumps(structured_context, ensure_ascii=False)}"
                ),
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "Answer using only the supplied structured context. Do not invent "
                        "prices, buyers, harbour capacity, or auction results. Say when "
                        "information is unavailable. Clearly mention DEMO/prototype data "
                        "when applicable. Never calculate or change factual market numbers "
                        "or a decision score; repeat a supplied deterministic score only. "
                        "Do not describe any indicative opportunity as guaranteed profit."
                    )
                ),
            )
            answer = (response.text or "").strip()
            if not answer:
                raise RuntimeError("Gemini returned an empty response.")
            return answer
        except Exception as exc:
            raise RuntimeError("AI provider request failed.") from exc
