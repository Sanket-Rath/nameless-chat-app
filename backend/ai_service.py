import google.generativeai as genai

from backend.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    "gemini-2.5-flash",
    system_instruction="You are a helpful assistant.",
)


def generate_response(message: str) -> str:
    try:
        response = model.generate_content(
            message,
            generation_config=genai.GenerationConfig(
                max_output_tokens=2000,
                temperature=0.8,
            ),
        )
        return response.text.strip()
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"
