from openai import OpenAI

from app.config import get_settings


def get_openai_client() -> OpenAI:
    settings = get_settings()

    if not settings.openai_api_key:
        raise RuntimeError(
            "Missing environment variable: OPENAI_API_KEY. "
            "Add it to backend/.env before running AI extraction."
        )

    return OpenAI(api_key=settings.openai_api_key)
