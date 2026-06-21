import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_URL = os.getenv("BASE_URL","https://api.deepseek.com")
    TIMEOUT = int(os.getenv("TIMEOUT", 30))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES",3))
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    API_KEY = os.getenv("API_KEY", "")
    API_SECRET = os.getenv("API_SECRET", "")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionCOnfig(Config):
    DEBUG = False

def get_config():
    env = os.getenv("ENV", "development")
    if env == "production":
        return ProductionCOnfig()
    return DevelopmentConfig()