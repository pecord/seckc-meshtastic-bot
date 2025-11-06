# Contributing to Meshtastic Bot

Thanks for your interest in contributing! This bot is designed to be easy to understand and extend.

## Project Structure

```
seckc-meshtastic-bot/
├── bot.py                    # Main entry point
├── personalities/            # Game modes (extend here!)
│   ├── base.py              # Base class for new personalities
│   └── trivia.py            # Trivia game implementation
├── services/                # External integrations
│   ├── config.py             # Environment config
│   ├── database.py          # SQLite
│   ├── meshtastic.py        # Device I/O
│   └── llm.py               # AI chat
└── data/
    ├── trivia_questions.txt # Question bank
    └── bot.db              # SQLite database (auto-created)
```

## Getting Started

### Prerequisites
- Python 3.9+
- A Meshtastic device connected via USB
- (Optional) Ollama for AI chat features

### Setup
```bash
# Clone and enter directory
cd seckc-meshtastic-bot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure
cp .env.example .env
# Edit .env with your settings

# Run the bot
python bot.py
```

## How to Contribute

### Creating a New Personality

The personality system makes it easy to add new game modes:

1. **Create a new file** in `personalities/` (e.g., `riddle.py`)

2. **Inherit from `Personality`**:
```python
from personalities.base import Personality

class RiddlePersonality(Personality):
    def __init__(self, database):
        super().__init__(database)
        self.name = "Riddle"
        # Your initialization
    
    def handle_message(self, text, sender_id, sender_name):
        """
        Process incoming messages and return response.
        
        Args:
            text: Message content
            sender_id: Meshtastic node ID
            sender_name: User's display name
            
        Returns:
            Response string or None to ignore
        """
        # Your game logic here
        if text.lower() == "!riddle":
            return "🤔 I speak without a mouth..."
        
        return None
```

3. **Wire it up** in `bot.py`:
```python
from personalities.riddle import RiddlePersonality

# In __init__:
self.personality = RiddlePersonality(self.db)
```

### Adding Questions

Edit `data/trivia_questions.txt`:

```
Q: Your question here?
A: first answer
A: second answer

Q: Next question?
A: answer
```

- Multiple answers per question are supported
- Answers are case-insensitive
- Empty lines are ignored

### Extending Services

Services are modular and easy to extend:

- **`services/meshtastic.py`** - Add new messaging features
- **`services/llm.py`** - Customize AI behavior
- **`services/database.py`** - Add new tables/queries

Each service is self-contained with clear interfaces.

## Code Style

- **Docstrings**: All classes and public methods should have docstrings
- **Type hints**: Optional but appreciated
- **Comments**: Explain *why*, not *what*
- **Simple over clever**: Readability matters for community contributions

## Testing

Before submitting:

```bash
# Run the bot
python bot.py

# Test from another device:
# - Send DM with "!help"
# - Send DM with "!trivia"
# - Answer a question
# - Check "!leaderboard"
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/cool-personality`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push and open a PR

## Ideas for Contributions

### Personalities
- **Scavenger Hunt**: GPS-based challenges
- **Math Quiz**: Quick calculation games
- **Word Games**: Hangman, word scrambles
- **Riddles**: Classic riddle game
- **Poll Bot**: Community voting system

### Features
- Web dashboard for leaderboards
- Multi-language support
- Admin commands (reset scores, broadcast)
- Scheduled events (daily challenges)
- Integration with other mesh services

### Improvements
- Better error handling
- Performance optimizations
- Extended documentation
- Example configurations
- Unit tests

## Questions?

- **Issues**: Open a GitHub issue
- **Discussions**: Use GitHub Discussions
- **Security**: Email security issues privately

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Happy hacking! 🚀
