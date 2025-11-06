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

# Hacker Jeopardy settings
HJ_ADMIN_NODE_IDS = os.getenv('HJ_ADMIN_NODE_IDS', '').split(',')  # Comma-separated list
# Clean up user IDs - remove leading ! if present and strip whitespace
# These are Meshtastic user IDs (shown with ! prefix in app), not node numbers
HJ_ADMIN_NODE_IDS = [node_id.strip().lstrip('!') for node_id in HJ_ADMIN_NODE_IDS if node_id.strip()]
HJ_QUESTIONS_FILE = os.getenv('HJ_QUESTIONS_FILE', 'data/hacker_jeopardy_questions.txt')
# Timing (in seconds)
HJ_QUESTION_INTERVAL = int(os.getenv('HJ_QUESTION_INTERVAL', '180'))  # Time between posting questions (not used with new flow)
HJ_ANSWER_WINDOW = int(os.getenv('HJ_ANSWER_WINDOW', '120'))  # Seconds to answer each question (2 min)
HJ_JOIN_WINDOW = int(os.getenv('HJ_JOIN_WINDOW', '30'))  # Seconds for players to join before game starts
HJ_BREAK_BETWEEN_QUESTIONS = int(os.getenv('HJ_BREAK_BETWEEN_QUESTIONS', '60'))  # 1 min break after revealing answer
HJ_MAX_ROUNDS = int(os.getenv('HJ_MAX_ROUNDS', '10'))  # Default 10 questions per game
HJ_GAME_CHANNEL_NAME = os.getenv('HJ_GAME_CHANNEL_NAME', 'SecKC-Test')  # Channel for game announcements
