import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base Configuration"""
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", "change-me-salt-in-production")
    
    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///cortex.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Celery Configuration
    CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    
    # Google AI Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
    EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
    LLM_MODEL = os.getenv("LLM_MODEL", "gemma-4-26b-a4b-it")
    # GitHub Token
    @classmethod
    def get_github_token(cls):
        token = os.getenv("GITHUB_TOKEN")
        if token:
            return token
        try:
            import subprocess
            return subprocess.check_output(["gh", "auth", "token"]).decode("utf-8").strip()
        except Exception:
            return None

    GITHUB_TOKEN = get_github_token.__func__(None)
    
    # ChromaDB Configuration
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
    
    # Flask-Security configurations
    SECURITY_PASSWORD_HASH = "bcrypt"
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_TRACKABLE = False
    # Use headers for token-based auth
    SECURITY_TOKEN_AUTHENTICATION_HEADER = "Authorization"
    SECURITY_TOKEN_MAX_AGE = 86400  # 1 day
    SECURITY_FLASH_MESSAGES = False
    SECURITY_REDIRECT_BEHAVIOR = "spa"
    SECURITY_BLUEPRINT_REGISTER = False
    SECURITY_HTTP_AUTHENTICATION_SCHEMES = ["bearer"]
    SECURITY_UNAUTHORIZED_VIEW = None



class DevConfig(Config):
    """Development Configuration"""
    DEBUG = True
    TESTING = False

class ProdConfig(Config):
    """Production Configuration"""
    DEBUG = False
    TESTING = False
    # Force production database to fail if not set
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
