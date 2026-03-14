import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

GWDG_BASE_URL = "https://chat-ai.academiccloud.de/v1"
DEFAULT_MODEL = "meta-llama-3.1-8b-instruct"

_client = None


def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GWDG_API_KEY")
        if not api_key:
            raise ValueError("GWDG_API_KEY not set in environment")
        _client = OpenAI(
            api_key=api_key,
            base_url=GWDG_BASE_URL,
        )
    return _client


def chat_completion(messages, model=None, temperature=0.0, max_tokens=1024):
    client = get_client()
    response = client.chat.completions.create(
        messages=messages,
        model=model or DEFAULT_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content
