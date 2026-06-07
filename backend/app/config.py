import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base Configuration"""
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", "change-me-salt-in-production")
    
    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/cortex")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Celery Configuration
    CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    
    # Google AI Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
    EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
    LLM_MODEL = os.getenv("LLM_MODEL", "gemma-4-26b-a4b-it")
    
    # GitHub Token
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
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
