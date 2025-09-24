import os
from dotenv import load_dotenv

load_dotenv() 

# 1. APPLICATION SECURITY KEY
SECRET_KEY = os.environ.get("SECRET_KEY", "fallback_secret_key_for_dev_only")

# 2. DATABASE CONNECTION SETTINGS
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.environ.get("DB_NAME", "Guess_Game")

# 3. GAME SETTINGS
# Note: os.environ.get returns a string, so we convert it to an integer.
GUEST_TTL_SECONDS = int(os.environ.get("GUEST_TTL_SECONDS", 3600))