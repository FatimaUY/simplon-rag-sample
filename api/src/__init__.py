"""RAG package."""
from dotenv import load_dotenv
import os

# Charger le .env à l'import du package
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(_env_path)