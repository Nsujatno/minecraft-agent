import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")  # shared with bot/

WS_URL = f"ws://127.0.0.1:{os.getenv('WS_PORT', '8080')}"
RECONNECT_SECONDS = 2.0

# OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_LLM_CALLS = int(os.getenv("MAX_LLM_CALLS", "50"))  # hard session cap — PRD cost control
HISTORY_TURNS = int(os.getenv("HISTORY_TURNS", "10"))
