import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = os.getenv("OPENAI_API_BASE")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")

if not API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in .env file. Please set it to continue.")
