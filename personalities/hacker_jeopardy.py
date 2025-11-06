"""
Hacker Jeopardy Personality - Live game show for mesh networks

A live trivia game experience with timed rounds, point values, and
AI-powered host commentary. Designed for SecKC meetups and hacker gatherings.

Features:
- Timed rounds with automatic question posting
- Point-based scoring (correct = +points, wrong = -points)
- AI host with personality and commentary
- Admin controls for game management
- Anti-spam and ban system
- Session-based leaderboards

Game Flow:
1. Admin starts game with !hj start
2. Bot posts LLM-generated intro with rules
3. Questions posted to channel every X minutes
4. Players DM answers within time window
5. Bot reveals answer and scores
6. Game ends after N rounds or admin command
7. Final leaderboard posted

Commands:
**Admin Commands (DM only):**
- `!hj start` - Start a new game session
- `!hj stop` - End current game and show final scores
- `!hj next` - Skip current question
- `!hj ban <user_id>` - Ban a player (use their !12345678 ID)
- `!hj unban <user_id>` - Unban a player
- Players: !hj join (rules), !hj status, !hj scores
"""
import random
import threading
from datetime import datetime, timedelta
from personalities.base import Personality
from services import config


def timestamp():
    """Get current timestamp for logging"""
    return datetime.now().strftime("%H:%M:%S")


class HackerJeopardyPersonality(Personality):
    """
    Live Hacker Jeopardy game personality with AI host.
    
    Manages game state, timing, scoring, and player interactions.
    Uses LLM service for entertaining host commentary.
    """
    
    # Game states
    STATE_IDLE = "IDLE"
    STATE_ACTIVE = "ACTIVE"
    STATE_COLLECTING_ANSWERS = "COLLECTING_ANSWERS"
    
    def __init__(self, database, meshtastic_service, llm_service=None,
                 questions_file=None, admin_node_ids=None):
        """
        Initialize Hacker Jeopardy personality.
        
        Args:
            database: BotDatabase instance
            meshtastic_service: MeshtasticService for channel posting
            llm_service: LLM service for host commentary (optional)
            questions_file: Path to questions file
            admin_node_ids: List of admin node IDs
        """
        super().__init__(database)
        self.name = "Hacker Jeopardy"
        
        # Services
        self.mesh = meshtastic_service
        self.llm = llm_service
        
        # Configuration
        self.questions_file = questions_file or config.HJ_QUESTIONS_FILE
        self.admin_node_ids = admin_node_ids or config.HJ_ADMIN_NODE_IDS  # User IDs, not node numbers
        self.game_channel_name = config.HJ_GAME_CHANNEL_NAME
        self.answer_window = config.HJ_ANSWER_WINDOW
        self.break_between_questions = config.HJ_BREAK_BETWEEN_QUESTIONS
        self.max_rounds = config.HJ_MAX_ROUNDS
        
        # Game state
        self.state = self.STATE_IDLE
        self.session_id = None
        self.current_question = None
        self.current_answers = []
        self.current_point_value = 0
        self.current_question_db_id = None
        self.question_closes_at = None
        self.questions = self.load_questions(self.questions_file)
        self.used_questions = set()
        
        # Timers
        self.question_timer = None
        self.close_timer = None
        
        # Channel tracking
        self.game_channel_index = None
        
        print(f"🎮 Hacker Jeopardy initialized")
        print(f"   Admins: {', '.join(self.admin_node_ids) if self.admin_node_ids else 'NONE CONFIGURED'}")
        print(f"   Questions: {len(self.questions)} loaded")
        print(f"   Timing: {self.answer_window}s answer window, {self.break_between_questions}s break between questions")
    
    def load_questions(self, filepath):
        """
        Load questions with point values from file.
        Format: 
        Q:100: What port does SSH use?
        A: 22
        A: twenty-two
        
        Q:200: What does XSS stand for?
        A: cross-site scripting
        """
        questions = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                current_q = None
                current_points = 100
                current_answers = []
                
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if line.startswith('Q:'):
                        # Save previous question
                        if current_q and current_answers:
                            questions.append((current_q, current_answers, current_points))
                        
                        # Parse new question: Q:100: question text
                        parts = line[2:].split(':', 1)
                        if len(parts) == 2 and parts[0].strip().isdigit():
                            current_points = int(parts[0].strip())
                            current_q = parts[1].strip()
                        else:
                            # No point value specified, default to 100
                            current_points = 100
                            current_q = line[2:].strip()
                        current_answers = []
                        
                    elif line.startswith('A:'):
                        current_answers.append(line[2:].strip().lower())
                
                # Don't forget last question
                if current_q and current_answers:
                    questions.append((current_q, current_answers, current_points))
        
        except FileNotFoundError:
            print(f"⚠️  Warning: {filepath} not found. Using default questions.")
            questions = [
                ("What port does SSH use by default?", ["22", "twenty-two"], 100),
                ("What does XSS stand for?", ["cross-site scripting", "cross site scripting"], 200),
                ("What is the default port for HTTPS?", ["443", "four forty-three"], 100),
            ]
        
        return questions
    
    def is_admin(self, user_id):
        """Check if user_id is an admin (handles both !12345 and 12345 formats)"""
        # Strip leading ! from user_id if present
        # user_id comes from packet['fromId'] which is the Meshtastic user ID
        clean_id = str(user_id).lstrip('!')
        # Also check against admin IDs (already cleaned in config)
        return clean_id in self.admin_node_ids
    
    def get_channel_index(self):
        """Get the channel index for game announcements"""
        if self.game_channel_index is not None:
            return self.game_channel_index
        
        # Use the meshtastic service's method to find the channel
        self.game_channel_index = self.mesh.find_channel_by_name(self.game_channel_name)
        
        if self.game_channel_index is None:
            print(f"⚠️  Channel '{self.game_channel_name}' not found. Using channel 0.")
            self.game_channel_index = 0
        
        return self.game_channel_index
        return 0
    
    def post_to_channel(self, message):
        """Post a message to the game channel"""
        channel_idx = self.get_channel_index()
        self.mesh.send_text(message, channel_index=channel_idx)
        print(f"[{timestamp()}] 📢 [Channel {channel_idx}] {message}")
    
    def start_game(self, admin_node_id):
        """Start a new game session"""
        if self.state != self.STATE_IDLE:
            return "⚠️ Game already in progress!"
        
        # Debug: show what we're checking
        clean_id = str(admin_node_id).lstrip('!')
        print(f"[{timestamp()}] 🔐 Admin check: '{admin_node_id}' (cleaned: '{clean_id}') vs {self.admin_node_ids}")
        
        if not self.is_admin(admin_node_id):
            return "❌ Only admins can start games!"
        
        # Create new session
        self.session_id = self.db.create_hj_session(self.max_rounds)
        self.state = self.STATE_ACTIVE
        self.used_questions = set()
        
        # Post game announcement to channel
        intro = f"""🎮 HACKER JEOPARDY - GAME ON!

Send !join to play! You can join anytime.
Questions posted here + DM'd to players.
DM your answers back to me.

Correct = +points | Wrong = -points
{self.max_rounds} rounds total. Good luck! 🚀"""
        
        self.post_to_channel(intro)
        
        # Start first question after join window
        self.schedule_next_question(delay=30)  # 30 seconds for players to join
        
        return f"✅ Game #{self.session_id} started! Players can !join"
    
    def stop_game(self, admin_node_id):
        """Stop the current game"""
        if self.state == self.STATE_IDLE:
            return "⚠️ No game in progress!"
        
        if not self.is_admin(admin_node_id):
            return "❌ Only admins can stop games!"
        
        # Cancel timers
        if self.question_timer:
            self.question_timer.cancel()
        if self.close_timer:
            self.close_timer.cancel()
        
        # End session
        if self.session_id:
            self.db.end_hj_session(self.session_id)
        
        # Post final scores
        self.post_final_scores()
        
        # Reset state
        self.state = self.STATE_IDLE
        self.session_id = None
        self.current_question = None
        
        return "✅ Game stopped!"
    
    def schedule_next_question(self, delay=None):
        """Schedule the next question to be posted"""
        if delay is None:
            delay = self.break_between_questions
        
        next_time = datetime.now() + timedelta(seconds=delay)
        print(f"[{timestamp()}] ⏰ Scheduling next question in {delay}s (at {next_time.strftime('%H:%M:%S')})")
        self.question_timer = threading.Timer(delay, self.post_question)
        self.question_timer.daemon = True
        self.question_timer.start()
    
    def post_question(self):
        """Post a new question to the channel"""
        print(f"[{timestamp()}] 📝 post_question() called, state={self.state}")
        if self.state == self.STATE_IDLE:
            print(f"[{timestamp()}] ⚠️  State is IDLE, not posting question")
            return
        
        # Check if we've reached max rounds
        session_info = self.db.get_hj_session_info(self.session_id)
        if session_info:
            current_round, max_rounds, status = session_info
            if current_round >= max_rounds:
                # Game over
                self.post_to_channel("🏁 Final round complete!")
                self.post_final_scores()
                self.state = self.STATE_IDLE
                self.db.end_hj_session(self.session_id)
                return
        
        # Pick a random unused question
        available = [q for i, q in enumerate(self.questions) if i not in self.used_questions]
        if not available:
            self.post_to_channel("📚 Out of questions!")
            self.stop_game(self.admin_node_ids[0] if self.admin_node_ids else "")
            return
        
        q_text, answers, points = random.choice(available)
        q_idx = self.questions.index((q_text, answers, points))
        self.used_questions.add(q_idx)
        
        # Store current question
        self.current_question = q_text
        self.current_answers = answers
        self.current_point_value = points
        self.question_closes_at = (datetime.now() + timedelta(seconds=self.answer_window)).isoformat()
        
        # Record in database
        question_id = f"hj_{self.session_id}_{q_idx}"
        self.current_question_db_id = self.db.record_hj_question(
            self.session_id, question_id, q_text, points,
            answers[0], self.question_closes_at
        )
        
        # Generate question announcement
        session_info = self.db.get_hj_session_info(self.session_id)
        round_num = session_info[0] if session_info else 0
        
        msg = f"❓ ROUND {round_num}/{self.max_rounds} - {points} POINTS\n{q_text}\n\n"
        msg += f"⏱️ DM your answer within {self.answer_window // 60} minutes!"
        
        # Post to channel
        self.post_to_channel(msg)
        
        # DM question to all players
        players = self.db.get_session_players(self.session_id)
        dm_msg = f"❓ ROUND {round_num}/{self.max_rounds} - {points} pts\n{q_text}"
        for user_id, username in players:
            try:
                self.mesh.send_text(dm_msg, destination=user_id)
                print(f"[{timestamp()}] 📤 Sent question to {username}")
            except Exception as e:
                print(f"[{timestamp()}] ⚠️  Failed to DM {username}: {e}")
        
        self.state = self.STATE_COLLECTING_ANSWERS
        
        # Schedule answer window close
        close_time = datetime.now() + timedelta(seconds=self.answer_window)
        print(f"[{timestamp()}] ⏱️  Answer window closes at {close_time.strftime('%H:%M:%S')}")
        self.close_timer = threading.Timer(self.answer_window, self.close_question)
        self.close_timer.daemon = True
        self.close_timer.start()
    
    def close_question(self):
        """Close the current question and reveal answer"""
        print(f"[{timestamp()}] 🔒 close_question() called, state={self.state}")
        if self.state != self.STATE_COLLECTING_ANSWERS:
            print(f"[{timestamp()}] ⚠️  State is not COLLECTING_ANSWERS, returning")
            return
        
        # Reveal answer in channel
        reveal_msg = f"✅ Answer: {self.current_answers[0]}"
        self.post_to_channel(reveal_msg)
        
        # Clear current question
        self.current_question = None
        self.current_answers = []
        self.current_point_value = 0
        self.current_question_db_id = None
        self.state = self.STATE_ACTIVE
        
        # Schedule next question
        self.schedule_next_question()
    
    def process_answer(self, text, sender_id, sender_name):
        """
        Process a player's answer (via DM).
        
        Returns:
            Response message to send back to player
        """
        # Check if banned
        if self.db.is_banned(sender_id):
            return "🚫 You are banned from playing."
        
        # Check if game is active and collecting answers
        if self.state != self.STATE_COLLECTING_ANSWERS:
            if self.state == self.STATE_IDLE:
                return "⏸️ No game in progress. Wait for an admin to start one!"
            else:
                return "⏳ No active question right now. Wait for the next one!"
        
        # Check if answer window is still open
        if datetime.now().isoformat() > self.question_closes_at:
            return "⏰ Too late! Answer window closed."
        
        text_lower = text.lower().strip()
        
        # Check if answer is correct
        is_correct = text_lower in self.current_answers
        points_awarded = self.current_point_value if is_correct else -self.current_point_value
        
        # Record answer
        recorded = self.db.record_hj_answer(
            self.session_id, self.current_question_db_id,
            sender_id, sender_name, text, points_awarded
        )
        
        if not recorded:
            return "⚠️ You already answered this question!"
        
        # Return feedback
        if is_correct:
            return f"✅ Correct! +{self.current_point_value} points! 🎉"
        else:
            return f"❌ Wrong! -{self.current_point_value} points.\nCorrect answer: {self.current_answers[0]}"
    
    def handle_message(self, text, sender_id, sender_name):
        """
        Handle incoming messages.
        
        Channel messages: !hj commands
        DM messages: Answers or commands
        """
        text_lower = text.lower().strip()
        
        # Admin commands
        if text_lower == '!hj start':
            return self.start_game(sender_id)
        
        if text_lower == '!hj stop':
            return self.stop_game(sender_id)
        
        if text_lower == '!hj next':
            if not self.is_admin(sender_id):
                return "❌ Only admins can skip questions!"
            if self.close_timer:
                self.close_timer.cancel()
            self.close_question()
            return "⏭️ Question skipped!"
        
        if text_lower.startswith('!hj ban '):
            if not self.is_admin(sender_id):
                return "❌ Only admins can ban users!"
            target_id = text[8:].strip()
            self.db.ban_user(target_id, sender_id, "Admin ban")
            return f"🚫 Banned {target_id}"
        
        if text_lower.startswith('!hj unban '):
            if not self.is_admin(sender_id):
                return "❌ Only admins can unban users!"
            target_id = text[10:].strip()
            self.db.unban_user(target_id)
            return f"✅ Unbanned {target_id}"
        
        # Player commands
        if text_lower in ['!hj join', '!join']:
            if not self.session_id:
                return "⏸️ No game in progress. Wait for an admin to start one!"
            
            # Add player to session
            added = self.db.add_player_to_session(self.session_id, sender_id, sender_name)
            player_count = len(self.db.get_session_players(self.session_id))
            
            # If there's a current question, send it to the new player
            if added and self.current_question and self.state == self.STATE_COLLECTING_ANSWERS:
                session_info = self.db.get_hj_session_info(self.session_id)
                round_num = session_info[0] if session_info else 0
                
                dm_msg = f"❓ ROUND {round_num}/{self.max_rounds} - {self.current_point_value} pts\n{self.current_question}"
                try:
                    self.mesh.send_text(dm_msg, destination=sender_id)
                    print(f"[{timestamp()}] 📤 Sent current question to {sender_name}")
                except Exception as e:
                    print(f"[{timestamp()}] ⚠️  Failed to DM {sender_name}: {e}")
            
            if added:
                return f"✅ You're in! {player_count} players joined. Good luck! 🎮"
            else:
                return "👍 You're already in the game!"
        
        if text_lower in ['!hj help']:
            return self.get_help()
        
        if text_lower in ['!hj status', '!hj info']:
            return self.get_status()
        
        if text_lower in ['!hj scores', '!hj leaderboard']:
            return self.get_scores()
        
        # If not a command, treat as answer
        if not text_lower.startswith('!'):
            return self.process_answer(text, sender_id, sender_name)
        
        # Unknown command
        return f"❓ Unknown command. Use !hj help for commands."
    
    def get_help(self):
        """Return help text"""
        help_text = """🎮 HACKER JEOPARDY
Questions posted to channel.
DM your answers to me!

Correct = +points
Wrong = -points
No answer = 0

Commands:
!hj join - See rules
!hj status - Game info
!hj scores - Leaderboard"""
        
        if self.admin_node_ids:
            help_text += "\n\nAdmin: !hj start/stop"
        
        return help_text
    
    def get_status(self):
        """Return current game status"""
        if self.state == self.STATE_IDLE:
            return "⏸️ No game in progress."
        
        session_info = self.db.get_hj_session_info(self.session_id)
        if session_info:
            current_round, max_rounds, status = session_info
            return f"🎮 Game #{self.session_id}\nRound {current_round}/{max_rounds}\nStatus: {self.state}"
        
        return "🎮 Game in progress"
    
    def get_scores(self):
        """Return current session leaderboard"""
        if not self.session_id:
            return "⏸️ No game in progress."
        
        leaderboard = self.db.get_hj_session_leaderboard(self.session_id, limit=5)
        if not leaderboard:
            return "📊 No scores yet!"
        
        msg = "📊 LEADERBOARD:\n"
        for i, (username, points) in enumerate(leaderboard, 1):
            msg += f"{i}. {username}: {points} pts\n"
        
        return msg.rstrip()
    
    def post_final_scores(self):
        """Post final scores to channel"""
        if not self.session_id:
            return
        
        leaderboard = self.db.get_hj_session_leaderboard(self.session_id, limit=5)
        if not leaderboard:
            self.post_to_channel("🎮 Game over! No scores recorded.")
            return
        
        msg = "🏁 GAME OVER - FINAL SCORES:\n\n"
        for i, (username, points) in enumerate(leaderboard, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            msg += f"{emoji} {i}. {username}: {points} pts\n"
        
        msg += f"\nThanks for playing! 🎉"
        self.post_to_channel(msg)
    
    def generate_game_intro(self):
        """Generate game intro using LLM if available"""
        if not self.llm or not self.llm.is_available():
            return f"""🎮 HACKER JEOPARDY - GAME ON!

Questions posted every {self.question_interval // 60} mins.
You have {self.answer_window // 60} mins to DM your answer.

Correct = +points | Wrong = -points

{self.max_rounds} rounds total. Let's go! 🚀"""
        
        # Use LLM for entertaining intro
        system_prompt = """You are the charismatic host of Hacker Jeopardy, a live cybersecurity trivia game on a mesh network. Be enthusiastic, witty, and reference hacking culture. Keep response under 200 characters total. Be BRIEF but entertaining."""
        
        user_prompt = f"Welcome players to Hacker Jeopardy! Explain: questions every {self.question_interval // 60} mins, DM answers, {self.answer_window // 60} min window, correct = +points, wrong = -points, {self.max_rounds} rounds."
        
        try:
            intro = self.llm.chat(user_prompt, system_prompt=system_prompt)
            # Ensure it's not too long
            if len(intro) > 220:
                intro = intro[:217] + "..."
            return f"🎮 {intro}"
        except Exception as e:
            print(f"⚠️ LLM intro failed: {e}")
            # Fallback to default
            return f"""🎮 HACKER JEOPARDY - GAME ON!

Questions posted every {self.question_interval // 60} mins.
DM answers within {self.answer_window // 60} mins.

Correct = +points | Wrong = -points

{self.max_rounds} rounds. Let's hack! 🚀"""
