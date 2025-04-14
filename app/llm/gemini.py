import os
from google import genai
from google.genai import types
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Gemini:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Gemini, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.api_key = os.getenv("GEMINI_API_KEY")
            self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")

            if self.api_key is None:
                raise ValueError("GEMINI_API_KEY environment variable not set")

            self.client = genai.Client()
            self.initialized = True

    async def prompt_model(self, prompt: str, system_instruction: Optional[str] = None):
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            max_output_tokens=500,
            temperature=0.7,
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=f"{prompt}",
                config=config,
            )

            return response.text
        except Exception as e:
            logger.error(f"Error in prompt_model: {e}")

    async def prompt_file(self, bytes: bytes, prompt: str, mime_type: str):
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(
                    data=bytes,
                    mime_type=mime_type,
                ),
                prompt,
            ],
        )
        return response.text
