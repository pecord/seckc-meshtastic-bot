# Meshtastic Bot

A Python bot framework for Meshtastic mesh networks with swappable "personalities". Run trivia games, AI chat, and more on your mesh!

## ✨ Features

- 🎮 **Trivia Game** - Questions, scoring, and leaderboards
- 🤖 **AI Chat** - Flexible LLM integration via OpenAI-compatible APIs (Ollama, OpenAI, Azure, etc.)
- 💾 **Persistent Storage** - SQLite database with anti-cheat
- 📡 **Smart Routing** - DMs for commands, channels for public chat
- 🔌 **Auto-Discovery** - Auto-detects device, finds channels by name
- 🎨 **Extensible** - Easy-to-create personality system

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# (Optional) Install Ollama for local AI chat
brew install ollama
ollama pull gpt-oss:20b
ollama serve

# Configure (optional)
cp .env.example .env
# Edit .env to customize

# Run!
python bot.py
```

## 🎮 Usage

### Commands
**In DMs:**
- `!trivia` - Get a trivia question
- `!leaderboard` - View top 5 players
- `!llm <question>` - Ask AI a question
- Send an answer to score points (10 pts/question, one answer per question)

**In configured channel (e.g., "SecKC"):**
- `!llm <question>` - Ask AI (bot responds to channel)

### CLI Options
```bash
# Run with defaults (auto-detects device, uses local Ollama)
python bot.py

# Custom Ollama model
python bot.py --llm-model llama3.2:3b

# Use OpenAI instead of Ollama
python bot.py --llm-base-url https://api.openai.com/v1 --llm-model gpt-4 --llm-api-key sk-...

# Use a remote Ollama instance
python bot.py --llm-base-url http://192.168.1.100:11434/v1/ --llm-model llama3.2:3b
```

## ⚙️ Configuration

Create a `.env` file (copy from `.env.example`):

```bash
# LLM Settings (OpenAI-compatible endpoints)
LLM_BASE_URL=http://localhost:11434/v1  # Ollama default
LLM_MODEL=gpt-oss:20b
LLM_API_KEY=ollama  # Use 'ollama' for Ollama, or your API key for OpenAI/Azure
LLM_CHANNEL_NAME=SecKC

# Database & Trivia
DATABASE_PATH=data/bot.db
TRIVIA_QUESTIONS_FILE=data/trivia_questions.txt
POINTS_PER_QUESTION=10
```

**Supported LLM endpoints:**
- **Ollama** (local): `http://localhost:11434/v1/` (default)
- **OpenAI**: `https://api.openai.com/v1/`
- **Azure OpenAI**: Your Azure endpoint
- **Any OpenAI-compatible API**

**Priority:** Defaults → `.env` file → CLI arguments (highest)

## 📝 Adding Trivia Questions

Edit `data/trivia_questions.txt`:

```
Q: Your question here?
A: answer1
A: answer2

Q: Next question?
A: single answer
```

Restart the bot to load new questions. Users can only score once per question, regardless of which valid answer they give (anti-cheat via SQLite UNIQUE constraint).

## 🏗️ Architecture

**Modular service design:**
- `bot.py` - Main orchestrator & message routing
- `services/meshtastic.py` - Device auto-detection & communication
- `services/llm.py` - OpenAI-compatible LLM integration
- `services/database.py` - SQLite persistence with anti-cheat
- `personalities/trivia.py` - Game logic & commands

**Message routing:**
- DMs (channel 0): All commands work, bot replies via DM
- Configured channel: Only `!llm` works, bot replies to channel
- Other channels: Ignored (prevents spam)

## 🔮 Future Ideas

The personality system supports extensible game modes:
- Geo-guessing games
- Word puzzles
- Math challenges
- Custom event games
