from __future__ import annotations

import os

import google.generativeai as genai


class GeminiService:
    def configure(self) -> None:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    def build_model(self, *, model_name: str, system_instruction: str):
        self.configure()
        return genai.GenerativeModel(model_name=model_name, system_instruction=system_instruction)

