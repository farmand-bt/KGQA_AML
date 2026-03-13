import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = None


def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GWDG_API_KEY")
        if not api_key:
            raise ValueError("GWDG_API_KEY not set in environment")
        _client = OpenAI(
            api_key=api_key,
            base_url="https://chat-ai.academiccloud.de/v1",
        )
    return _client


def chat_completion(messages, model="meta-llama-3.1-8b-instruct", temperature=0.0, max_tokens=1024):
    client = get_client()
    response = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content
