import os
from google import genai
from google.genai import types
import logging

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
            self.model_name = "gemini-2.0-flash-001"

            if self.api_key is None:
                raise ValueError("GEMINI_API_KEY environment variable not set")

            self.client = genai.Client()
            self.initialized = True

    async def prompt_model(self, prompt, system_intruction=None):
        config = types.GenerateContentConfig(
            system_instruction=system_intruction,
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

    async def prompt_file(self, bytes, prompt):
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(
                    data=bytes,
                    mime_type="application/pdf",
                ),
                prompt,
            ],
        )
        return response.text
