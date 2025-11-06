# Meshtastic Bot

A Python bot framework for Meshtastic mesh networks with swappable "personalities". Run trivia games, AI chat, and more on your mesh!

## ✨ Features

- 🎮 **Trivia Game** - Questions, scoring, and leaderboards
- 🎯 **Hacker Jeopardy** - Live timed game show for meetups
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

# Run Hacker Jeopardy mode
python bot.py --personality hacker_jeopardy

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

## 🎯 Hacker Jeopardy Mode

A live, timed game show for hacker meetups! Perfect for SecKC and similar gatherings.

### How It Works

1. **Admin starts the game** with `!hj start`
2. **Bot posts questions** to the channel every 3 minutes (configurable)
3. **Players DM their answers** to the bot within the 2-minute answer window
4. **Scoring:**
   - ✅ Correct answer = **+points** (question value: 100-500)
   - ❌ Wrong answer = **-points** (same value)
   - No answer = **0 points** (no penalty)
5. **After each round**, bot reveals the answer and top 3 scores
6. **Game ends** after 10 rounds (configurable) or when admin runs `!hj stop`
7. **Final leaderboard** posted to channel

### Commands

**Admin Commands (DM only):**
- `!hj start` - Start a new game session
- `!hj stop` - End current game and show final scores
- `!hj next` - Skip current question
- `!hj ban <user_id>` - Ban a player (use their !12345678 ID from app)
- `!hj unban <user_id>` - Unban a player

**Player Commands (DM only):**
- `!hj join` - Show rules and how to play
- `!hj status` - Current game status
- `!hj scores` - View current leaderboard
- Just send your answer as a regular message (no command needed!)

**Game Flow:**
```
Questions posted to channel → Players DM answers → Bot scores in real-time → 
Answer revealed after time window → Next question → ... → Final scores
```

### Setup

1. **Set admin user IDs** in `.env`:
   ```bash
   HJ_ADMIN_NODE_IDS=!12345678,!87654321
   ```
   Get your user ID from the Meshtastic app:
   - **Mobile app**: Users tab → Long press your name → Shows "!12345678"
   - **Web interface**: Click on your node → User ID shown with ! prefix
   - You can include or omit the `!` prefix - both formats work

2. **Configure channel** (default: SecKC-Test):
   ```bash
   HJ_GAME_CHANNEL_NAME=SecKC-Test
   ```

3. **Customize timing** (optional):
   ```bash
   HJ_QUESTION_INTERVAL=180  # Seconds between questions (3 min)
   HJ_ANSWER_WINDOW=120       # Seconds to answer (2 min)
   HJ_MAX_ROUNDS=10          # Questions per game
   ```

4. **Add questions** to `data/hacker_jeopardy_questions.txt`:
   ```
   Q:100: What port does SSH use by default?
   A: 22
   A: twenty-two

   Q:200: What does XSS stand for?
   A: cross-site scripting
   A: cross site scripting

   Q:500: What is the CVE number for Heartbleed?
   A: cve-2014-0160
   A: 2014-0160
   ```

5. **Run the bot**:
   ```bash
   python bot.py --personality hacker_jeopardy
   ```

### LLM Host Feature

If an LLM service is available, the bot uses AI to generate entertaining game intros with hacker personality:

> "🎮 Alright SecKC hackers! Time for Hacker Jeopardy! Questions every 3 mins, DM your answers in 2 mins. Correct = +pts, wrong = -pts. 10 rounds. Let's pwn this! 🚀"

The AI host keeps responses under 200 characters for mesh bandwidth limits.

### Anti-Spam & Security

- **Admin-only controls** - Only configured node IDs can start/stop games
- **Ban system** - Admins can ban disruptive players
- **One answer per question** - Players can't spam multiple answers
- **Late answers ignored** - No penalty for answering after time window closes

### Tips for Running a Great Game

- **Test beforehand** - Run a practice game to check timing
- **Announce in advance** - Let people know when the game starts
- **Mix difficulties** - Use a variety of 100-500 point questions
- **Keep it moving** - 3-minute intervals keep energy high
- **Have prizes** - Small prizes for winners increase engagement!

## 🏗️ Architecture

**Modular service design:**
- `bot.py` - Main orchestrator & message routing
- `services/meshtastic.py` - Device auto-detection & communication
- `services/llm.py` - OpenAI-compatible LLM integration
- `services/database.py` - SQLite persistence with anti-cheat
- `services/config.py` - Configuration management
- `personalities/base.py` - Personality interface
- `personalities/trivia.py` - Casual trivia game
- `personalities/hacker_jeopardy.py` - Live timed game show

**Message routing:**
- DMs (channel 0): All commands work, bot replies via DM
- Configured channel: Game announcements (HJ mode) or `!llm` (trivia mode)
- Other channels: Ignored (prevents spam)

**Personality system:**
Each personality inherits from `base.Personality` and implements:
- `handle_message(text, sender_id, sender_name)` - Process messages
- `get_help()` - Return help text

The bot routes messages to the active personality and sends responses back.

## 🔮 Creating Custom Personalities

Want to build your own game or interaction? It's easy!

```python
from personalities.base import Personality

class MyPersonality(Personality):
    def __init__(self, database, **kwargs):
        super().__init__(database)
        self.name = "My Cool Game"
    
    def handle_message(self, text, sender_id, sender_name):
        if text.lower() == '!hello':
            return f"Hello {sender_name}!"
        return None  # No response
    
    def get_help(self):
        return "Say !hello to get a greeting!"
```

Then update `bot.py` to import and use your personality!

## 🔮 Future Ideas

The personality system supports extensible game modes:
- Geo-guessing games
- Word puzzles / Wordle
- Math challenges
- CTF scoreboard integration
- Custom event games
