import os
from dotenv import load_dotenv
from litellm import completion

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE")
model = os.getenv("OPENAI_MODEL_NAME")

print(f"Testing model: {model}")
print(f"Base URL: {api_base}")

try:
    response = completion(
        model=f"openai/{model}",
        messages=[{"role": "user", "content": "Hello, are you working?"}],
        api_key=api_key,
        base_url=api_base
    )
    print("Response received:")
    print(response)
except Exception as e:
    print(f"Error: {e}")
