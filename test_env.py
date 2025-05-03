import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
print("🧪 Looking for .env at:", env_path)

load_dotenv(dotenv_path=env_path)

key = os.getenv("OPENROUTER_API_KEY")
print("✅ OPENROUTER_API_KEY:", key)
