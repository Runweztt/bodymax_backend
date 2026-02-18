import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
PINDO_API_TOKEN = os.getenv("PINDO_API_TOKEN")
PINDO_SENDER = os.getenv("PINDO_SENDER", "BodyMax")
