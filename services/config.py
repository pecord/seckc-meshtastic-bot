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

# Ollama settings
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'gpt-oss:20b')
OLLAMA_CHANNEL_NAME = os.getenv('OLLAMA_CHANNEL_NAME', 'SecKC-Test')
