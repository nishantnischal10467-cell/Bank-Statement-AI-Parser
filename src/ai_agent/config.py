import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file first
load_dotenv(override=False)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    model_vision: str = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")
    model_text: str = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o")
    max_pages: int = int(os.getenv("MAX_PAGES", "6"))
    image_max_px: int = int(os.getenv("IMAGE_MAX_PX", "1600"))
    llm_timeout_s: int = int(os.getenv("LLM_TIMEOUT_S", "60"))


def get_settings() -> Settings:
    return Settings()

