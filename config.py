import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# API Key per Google Gemini Pro
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Impostazioni Audio
SAMPLE_RATE = 16000
CHANNELS = 1

# Impostazioni UI
BADGE_RADIUS = 25
