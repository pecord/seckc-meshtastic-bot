# Meshtastic Bot

A Python bot framework for Meshtastic mesh networks with swappable "personalities". Run trivia games, AI chat, and more on your mesh!

## ✨ Features

- 🎮 **Trivia Game** - Questions, scoring, and leaderboards
- 🤖 **AI Chat** - Local LLM integration via Ollama
- 💾 **Persistent Storage** - SQLite database for scores
- 🛡️ **Anti-Cheat** - One answer per question per player
- 📡 **Smart Routing** - DMs for commands, channels for public chat
- 🔌 **Auto-Discovery** - Finds channels by name, auto-detects device
- 🎨 **Extensible** - Easy-to-create personality system

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                    bot.py                       │
│              (Main Orchestrator)                │
└────────┬────────────────────────────────────────┘
         │
    ┌────┴──────┬──────────┬──────────────┐
    │           │          │              │
    ▼           ▼          ▼              ▼
┌────────┐ ┌─────────┐ ┌────────┐  ┌──────────┐
│Database│ │Meshtastic│ │ Ollama │  │Personality│
│Service │ │ Service │ │Service │  │  Layer   │
└────────┘ └─────────┘ └────────┘  └──────────┘
    │           │           │             │
    ▼           ▼           ▼             ▼
[SQLite]  [USB Device] [Local LLM]  [Game Logic]
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Meshtastic device (USB)
- (Optional) [Ollama](https://ollama.ai) for AI chat

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/seckc-meshtastic-bot
cd seckc-meshtastic-bot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure (optional)
cp .env.example .env
# Edit .env to customize settings

# Run!
python bot.py
```

## 📖 How It Works

The bot uses a modular service architecture:

### Core Components

**`bot.py`** - Main orchestrator
- Connects to Meshtastic device (auto-detect or specified)
- Routes messages based on channel
- Handles graceful shutdown and reconnection

**`services/meshtastic.py`** - Device communication
- Auto-detection and connection with timeout
- Message sending (DMs and channels)
- Channel discovery by name
- Node information retrieval

**`services/ollama.py`** - AI integration
- Connects to local Ollama instance
- Validates model availability
- Handles chat requests with system prompts

**`services/database.py`** - Persistence
- SQLite wrapper for scores and anti-cheat
- User tracking and leaderboards
- UNIQUE constraints prevent duplicate scoring

**`services/config.py`** - Configuration
- Loads from `.env` file
- Provides sensible defaults
- CLI override support

**`personalities/trivia.py`** - Game logic
- Question loading and management
- Command handling (!trivia, !leaderboard, !ollama)
- Score tracking and validation
- AI chat integration

### Data Files

**`data/trivia_questions.txt`** - Question bank:
   ```
   Q: What is 2+2?
   A: 4
   A: four
   ```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install and run Ollama locally (for AI chat feature):
```bash
# macOS
brew install ollama
ollama pull gpt-oss:20b  # or any model you prefer
ollama serve
```

3. Configure the bot (optional):
```bash
cp .env.example .env
# Edit .env to set:
# - OLLAMA_MODEL (default: gpt-oss:20b)
# - OLLAMA_CHANNEL_NAME (default: SecKC-Test)
```

4. Connect your Meshtastic device via USB

5. Run the bot:
```bash
# Auto-detect device and use default settings
python bot.py

# Use custom Ollama settings
python bot.py --ollama-model llama3.2:3b --ollama-host http://localhost:11434

# See all options
python bot.py --help
```

## Command Line Options

The bot supports the following CLI arguments (override .env settings):

```
  --ollama-host URL
      Ollama server URL (default: http://localhost:11434)
  
  --ollama-model MODEL, -m MODEL
      Ollama model to use (default: gpt-oss:20b)
```

**Note:** The bot automatically detects your Meshtastic device via USB - no manual path needed!

### Examples

```bash
# Run with defaults (auto-detect device)
python bot.py

# Custom Ollama model
python bot.py --ollama-model llama2
python bot.py -m llama3.2:3b --ollama-host http://192.168.1.100:11434

# All options
python bot.py -d /dev/ttyACM0 -m llama3.2:3b
```

### Configuration Priority

Settings are loaded in this order (later overrides earlier):
1. **Defaults** in `config.py`
2. **Environment variables** / `.env` file
3. **CLI arguments** (highest priority)

## Usage

### Direct Messages (All Commands)
Users can DM the bot to access all features:

- **`!trivia`** - Get a new trivia question
- **`!leaderboard`** - View top 5 players
- **`!ollama <question>`** - Ask AI a question
- **`!help`** - Show available commands
- **Send an answer** - Bot checks if correct and awards points (10 pts per question)

### Configured Channel (AI Chat Only)
On the configured channel (e.g., "SecKC"):
- **`!ollama <question>`** - Ask AI a question (responds to channel)

### Example Session
```
User (DM): !trivia
Bot (DM): 🧠 TRIVIA: What is frozen water called?

User (DM): ice
Bot (DM): ✅ Correct, UserName! +10 points! 🎉

User (DM): ice
Bot (DM): You already answered this one, UserName! 😊

User (DM): !leaderboard
Bot (DM): 📊 TRIVIA LEADERBOARD:
     1. UserName: 10 pts

User (SecKC channel): !ollama why is the sky blue?
Bot (SecKC channel): 🤖 The sky appears blue because...
```

## Features

- ✅ Connect via USB to Meshtastic device
- ✅ Auto-discover channels by name (no hardcoded indices)
- ✅ DM responses for trivia commands
- ✅ Channel responses for `!ollama` on configured channel
- ✅ Local AI chat via Ollama integration
- ✅ Track user scores in SQLite database
- ✅ Prevent duplicate answers (one answer per question per user, even with multiple valid answers)
- ✅ Leaderboard system
- ✅ Multiple accepted answers per question
- ✅ Case-insensitive answer matching
- ✅ Automatic node name resolution
- ✅ Clean startup output with configuration summary
- ✅ Auto-exit on device disconnect

## Configuration

The bot uses a `.env` file for configuration:

```bash
# Ollama Settings
OLLAMA_MODEL=gpt-oss:20b
OLLAMA_HOST=http://localhost:11434

# Channel Settings
# Bot will find this channel by name automatically
OLLAMA_CHANNEL_NAME=SecKC

# Database
DATABASE_PATH=data/bot.db

# Trivia
TRIVIA_QUESTIONS_FILE=data/trivia_questions.txt
POINTS_PER_QUESTION=10
```

## Adding Questions

Edit `data/trivia_questions.txt` and add questions in this format:

```
Q: Your question here?
A: answer1
A: answer2
A: answer3

Q: Next question?
A: answer
```

**Note**: Multiple answers are accepted for user convenience, but users can only score once per question regardless of which valid answer they give.

Restart the bot to load new questions.

## Architecture Details

### Message Routing Logic

- **`!ollama` commands**:
  - On DM (channel 0) → Reply via DM
  - On configured channel → Reply to that channel
  - On other channels → Ignored

- **Trivia commands** (`!trivia`, `!leaderboard`, answers):
  - On DM (channel 0) → Reply via DM
  - On any channel → Ignored (no spam)

### Anti-Cheat System

The database prevents users from scoring multiple times on the same question:

1. Each question has a unique ID: `q_{hash(question_text)}`
2. Database has UNIQUE constraint: `(node_id, question_id)`
3. Multiple valid answers (e.g., "dog", "dogs") are for the SAME question
4. User can only score once per question, regardless of which valid answer they provide

## Files

- `bot.py` - Main bot runner with message routing
- `config.py` - Configuration loader (env vars + .env file)
- `database.py` - SQLite database wrapper
- `personalities/base.py` - Base personality class
- `personalities/trivia.py` - Trivia game + Ollama integration
- `data/trivia_questions.txt` - Question bank
- `data/bot.db` - SQLite database (auto-created)
- `.env` - Configuration file (create from .env.example)
- `.env.example` - Example configuration
- `requirements.txt` - Python dependencies
- `poc_test.py` - Proof of concept test script

## Future Personalities

The architecture supports swappable personalities. Future ideas:
- Geo-guessing game
- Word games
- Math challenges
- Custom games for events
