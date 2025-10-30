import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
AUTHJWT_SECRET_KEY = os.getenv("AUTHJWT_SECRET_KEY")
ENCODEING_SECRET_KEY = os.getenv("ENCODEING_SECRET_KEY").encode()

EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_TLS = os.getenv("EMAIL_TLS", "True").lower() == "true"
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

OPEN_AI_API = os.getenv("OPEN_AI_API")

CURRENT_SEMESTER = os.getenv("CURRENT_SEMESTER")
