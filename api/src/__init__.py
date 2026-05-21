"""RAG package."""

import os

from dotenv import load_dotenv

# Charger le .env à l'import du package
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(_env_path)
