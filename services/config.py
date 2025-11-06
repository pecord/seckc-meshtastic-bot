"""
Configuration Service - Environment and defaults

Loads configuration from .env file with sensible defaults.
All values can be overridden via command-line arguments.
"""
import os

# Try to load .env file
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv()
        print("✅ Loaded configuration from .env")
except ImportError:
    pass  # python-dotenv not installed, use environment variables only

# Configuration with defaults
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/bot.db')
TRIVIA_QUESTIONS_FILE = os.getenv('TRIVIA_QUESTIONS_FILE', 'data/trivia_questions.txt')

# LLM settings (OpenAI-compatible endpoints)
LLM_API_KEY = os.getenv('LLM_API_KEY', 'ollama')  # Use 'ollama' as default for Ollama
LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'http://localhost:11434/v1/')  # OpenAI-compatible endpoint (note trailing slash)
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-oss:20b')
LLM_CHANNEL_NAME = os.getenv('LLM_CHANNEL_NAME', 'SecKC-Test')
