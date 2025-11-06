"""
Trivia Personality - Question and answer game with AI chat

Features:
- Multiple choice trivia questions
- Persistent leaderboard
- Anti-cheat (one answer per question per player)
- AI chat integration via OpenAI-compatible LLM API
- Message chunking for Meshtastic size limits
"""
import random
from personalities.base import Personality


class TriviaPersonality(Personality):
    """
    Trivia game personality with AI chat support.
    
    Commands:
    - !trivia: Get a new question
    - !leaderboard: Show top scores
    - !help: Show available commands
    - !llm <question>: Ask AI (if available)
    
    Questions are loaded from a text file in Q:/A: format.
    Multiple answers per question are supported.
    """
    
    def __init__(self, database, questions_file="data/trivia_questions.txt", 
                 llm_service=None):
        """
        Initialize trivia personality.
        
        Args:
            database: BotDatabase instance
            questions_file: Path to questions file (Q:/A: format)
            llm_service: LLM service instance (optional)
        """
        super().__init__(database)
        self.name = "Trivia"
        self.questions = self.load_questions(questions_file)
        self.current_question = None
        self.current_answers = []
        self.current_question_id = None
        
        # Use injected LLM service
        self.llm = llm_service
    
    def load_questions(self, filepath):
        """
        Load questions from simple text file
        Format: 
        Q: What is 2+2?
        A: 4
        A: four
        
        Q: Next question?
        A: answer
        """
        questions = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                current_q = None
                current_answers = []
                
                for line in f:
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue
                        
                    if line.startswith('Q:'):
                        # Save previous question if exists
                        if current_q and current_answers:
                            questions.append((current_q, current_answers))
                        
                        current_q = line[2:].strip()
                        current_answers = []
                    elif line.startswith('A:'):
                        current_answers.append(line[2:].strip().lower())
                
                # Don't forget the last question
                if current_q and current_answers:
                    questions.append((current_q, current_answers))
        
        except FileNotFoundError:
            print(f"⚠️  Warning: {filepath} not found. Using default questions.")
            # Provide some default questions
            questions = [
                ("What is 2 + 2?", ["4", "four"]),
                ("What color is the sky?", ["blue"]),
                ("What is the capital of France?", ["paris"]),
            ]
        
        return questions
    
    def ask_new_question(self):
        """Pick a random question and return the message"""
        if not self.questions:
            return "No questions available!", None
        
        q, answers = random.choice(self.questions)
        self.current_question = q
        self.current_answers = answers
        self.current_question_id = f"q_{hash(q)}"
        
        return f"🧠 TRIVIA: {q}", self.current_question_id
    
    def handle_message(self, text, sender_id, sender_name):
        """Handle incoming messages and respond appropriately"""
        text_lower = text.lower().strip()
        
        # Command: Start new question
        if text_lower in ['!trivia', '!question', '!q']:
            msg, _ = self.ask_new_question()
            return msg
        
        # Command: Leaderboard
        if text_lower in ['!leaderboard', '!scores', '!top']:
            board = self.db.get_leaderboard(5)
            if not board:
                return "📊 No scores yet! Answer questions to get on the board!"
            
            msg = "📊 TRIVIA LEADERBOARD:\n"
            for i, (name, points) in enumerate(board, 1):
                msg += f"{i}. {name}: {points} pts\n"
            return msg.rstrip()
        
        # Command: Help
        if text_lower in ['!help', '!commands']:
            return self.get_help()
        
        # Command: LLM chat
        if text_lower.startswith('!llm '):
            if not self.llm or not self.llm.is_available():
                return "❌ LLM service not available. Check your configuration."
            
            prompt = text[5:].strip()  # Get everything after "!llm "
            
            if not prompt:
                return "🤖 Usage: !llm <question>\nExample: !llm what is meshtastic?"
            
            # Limit prompt length
            if len(prompt) > 500:
                return "❌ Prompt too long! Keep it under 500 characters."
            
            # Call LLM service with system prompt for concise responses
            system_prompt = 'You are a helpful assistant on a low-bandwidth mesh network. Keep responses under 200 characters. Be concise and direct.'
            answer = self.llm.chat(prompt, system_prompt=system_prompt)
            
            # Truncate if still too long (Meshtastic has limits)
            if len(answer) > 220:
                answer = answer[:217] + "..."
            
            return f"🤖 {answer}"
        
        # Check if answer is correct
        if self.current_question and self.current_answers and self.current_question_id:
            if text_lower in self.current_answers:
                # Try to award points (10 points per correct answer)
                awarded = self.db.add_points(
                    sender_id, 
                    sender_name, 
                    10, 
                    self.current_question_id
                )
                
                if awarded:
                    return f"✅ Correct, {sender_name}! +10 points! 🎉"
                else:
                    return f"You already answered this one, {sender_name}! 😊"
        
        # If message looks like a command but wasn't recognized, show help
        if text_lower.startswith('!'):
            return f"❓ Unknown command ({text_lower}).\n{self.get_help()}"
        
        return None  # No response for unrecognized messages
    
    def get_help(self):
        """Return help text"""
        help_text = """🧠 TRIVIA BOT COMMANDS:
!trivia - New question
!leaderboard - Top scores
!help - This message"""
        
        if self.llm and self.llm.is_available():
            help_text += "\n!llm <question> - Ask AI"
        
        return help_text
