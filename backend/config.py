import os
from dotenv import load_dotenv

load_dotenv()


def get_env_var(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"{name} environment variable must be set")
    return value

DATABASE_URL = get_env_var("DATABASE_URL")
SECRET_KEY = get_env_var("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY or GEMINI_API_KEY environment variable must be set")
GEMINI_API_KEY = OPENAI_API_KEY