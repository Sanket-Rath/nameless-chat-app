import openai

from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY


def generate_response(message: str) -> str:
    completion_client = getattr(openai, "Completion", None)
    if completion_client is None:
        raise RuntimeError("OpenAI Completion client is unavailable")

    response = completion_client.create(
        model="text-davinci-003",
        prompt=message,
        max_tokens=150,
        temperature=0.8
    )
    return response.choices[0].text.strip()