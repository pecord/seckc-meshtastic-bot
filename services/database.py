"""
Database Service - SQLite persistence layer

Manages user scores, leaderboards, and anti-cheat tracking.
Uses SQLite for simple, file-based persistence.
"""
import sqlite3
import os
from datetime import datetime


class BotDatabase:
    """
    SQLite database for bot persistence.
    
    Tables:
    - users: Player profiles and total points
    - user_answers: Answer history for anti-cheat (UNIQUE constraint)
    
    The UNIQUE(node_id, question_id) constraint ensures players
    can only score once per question.
    """
    
    def __init__(self, db_path='data/bot.db'):
        """
        Initialize database and create tables if needed.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.init_db()
    
    def init_db(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (node_id TEXT PRIMARY KEY,
                      username TEXT,
                      total_points INTEGER DEFAULT 0,
                      last_seen TEXT)''')
        
        # Answers table - tracks what each user has answered
        c.execute('''CREATE TABLE IF NOT EXISTS user_answers
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      node_id TEXT,
                      question_id TEXT,
                      answered_at TEXT,
                      UNIQUE(node_id, question_id))''')
        
        # Hacker Jeopardy game sessions
        c.execute('''CREATE TABLE IF NOT EXISTS hj_sessions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      started_at TEXT,
                      ended_at TEXT,
                      status TEXT,
                      max_rounds INTEGER,
                      current_round INTEGER DEFAULT 0)''')
        
        # Players who have joined a session
        c.execute('''CREATE TABLE IF NOT EXISTS hj_session_players
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      session_id INTEGER,
                      user_id TEXT,
                      username TEXT,
                      joined_at TEXT,
                      UNIQUE(session_id, user_id))''')
        
        # Questions posted in each session
        c.execute('''CREATE TABLE IF NOT EXISTS hj_session_questions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      session_id INTEGER,
                      question_id TEXT,
                      question_text TEXT,
                      point_value INTEGER,
                      posted_at TEXT,
                      closes_at TEXT,
                      correct_answer TEXT)''')
        
        # Player answers in each session
        c.execute('''CREATE TABLE IF NOT EXISTS hj_session_answers
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      session_id INTEGER,
                      question_id INTEGER,
                      node_id TEXT,
                      username TEXT,
                      answer_text TEXT,
                      points_awarded INTEGER,
                      answered_at TEXT,
                      UNIQUE(session_id, question_id, node_id))''')
        
        # Banned users
        c.execute('''CREATE TABLE IF NOT EXISTS banned_users
                     (node_id TEXT PRIMARY KEY,
                      banned_at TEXT,
                      banned_by TEXT,
                      reason TEXT)''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized: {self.db_path}")
    
    def add_points(self, node_id, username, points, question_id):
        """
        Add points if user hasn't answered this question before
        
        Returns:
            True if points were awarded
            False if user already answered this question
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            # Try to insert answer (will fail if duplicate)
            c.execute('''INSERT INTO user_answers (node_id, question_id, answered_at)
                        VALUES (?, ?, ?)''',
                     (node_id, question_id, datetime.now().isoformat()))
            
            # Update user points
            c.execute('''INSERT INTO users (node_id, username, total_points, last_seen)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(node_id) DO UPDATE SET
                        total_points = total_points + ?,
                        username = ?,
                        last_seen = ?''',
                     (node_id, username, points, datetime.now().isoformat(),
                      points, username, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True  # Points awarded!
        except sqlite3.IntegrityError:
            conn.close()
            return False  # Already answered this question
    
    def get_leaderboard(self, limit=10):
        """Get top users by points"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT username, total_points 
                    FROM users 
                    ORDER BY total_points DESC 
                    LIMIT ?''', (limit,))
        results = c.fetchall()
        conn.close()
        return results
    
    def get_user_stats(self, node_id):
        """Get stats for a specific user"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT username, total_points 
                    FROM users 
                    WHERE node_id = ?''', (node_id,))
        result = c.fetchone()
        conn.close()
        return result
    
    # ===== Hacker Jeopardy Methods =====
    
    def is_banned(self, node_id):
        """Check if a user is banned"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT node_id FROM banned_users WHERE node_id = ?', (node_id,))
        result = c.fetchone()
        conn.close()
        return result is not None
    
    def ban_user(self, node_id, banned_by, reason=""):
        """Ban a user from participating"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO banned_users (node_id, banned_at, banned_by, reason)
                    VALUES (?, ?, ?, ?)''',
                 (node_id, datetime.now().isoformat(), banned_by, reason))
        conn.commit()
        conn.close()
    
    def unban_user(self, node_id):
        """Unban a user"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM banned_users WHERE node_id = ?', (node_id,))
        conn.commit()
        conn.close()
    
    def create_hj_session(self, max_rounds):
        """Create a new Hacker Jeopardy game session"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO hj_sessions (started_at, status, max_rounds, current_round)
                    VALUES (?, ?, ?, ?)''',
                 (datetime.now().isoformat(), 'ACTIVE', max_rounds, 0))
        session_id = c.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def end_hj_session(self, session_id):
        """End a Hacker Jeopardy session"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''UPDATE hj_sessions SET ended_at = ?, status = ?
                    WHERE id = ?''',
                 (datetime.now().isoformat(), 'ENDED', session_id))
        conn.commit()
        conn.close()
    
    def record_hj_question(self, session_id, question_id, question_text, point_value, 
                          correct_answer, closes_at):
        """Record a question posted in a session"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO hj_session_questions 
                    (session_id, question_id, question_text, point_value, posted_at, closes_at, correct_answer)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (session_id, question_id, question_text, point_value, 
                  datetime.now().isoformat(), closes_at, correct_answer))
        db_question_id = c.lastrowid
        
        # Increment round counter
        c.execute('UPDATE hj_sessions SET current_round = current_round + 1 WHERE id = ?', 
                 (session_id,))
        conn.commit()
        conn.close()
        return db_question_id
    
    def record_hj_answer(self, session_id, question_id, node_id, username, 
                        answer_text, points_awarded):
        """
        Record a player's answer for a question
        
        Returns:
            True if answer was recorded
            False if player already answered this question
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''INSERT INTO hj_session_answers 
                        (session_id, question_id, node_id, username, answer_text, 
                         points_awarded, answered_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (session_id, question_id, node_id, username, answer_text,
                      points_awarded, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False  # Already answered this question
    
    def get_hj_session_leaderboard(self, session_id, limit=10):
        """Get leaderboard for a specific HJ session"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT username, SUM(points_awarded) as total_points
                    FROM hj_session_answers
                    WHERE session_id = ?
                    GROUP BY node_id, username
                    ORDER BY total_points DESC
                    LIMIT ?''', (session_id, limit))
        results = c.fetchall()
        conn.close()
        return results
    
    def get_hj_session_info(self, session_id):
        """Get session info including current round and max rounds"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT current_round, max_rounds, status
                    FROM hj_sessions
                    WHERE id = ?''', (session_id,))
        result = c.fetchone()
        conn.close()
        return result
    
    def add_player_to_session(self, session_id, user_id, username):
        """
        Add a player to a session
        
        Returns:
            True if player was added
            False if player was already in session
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''INSERT INTO hj_session_players (session_id, user_id, username, joined_at)
                        VALUES (?, ?, ?, ?)''',
                     (session_id, user_id, username, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False  # Already in session
    
    def get_session_players(self, session_id):
        """Get list of players in a session as (user_id, username) tuples"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT user_id, username
                    FROM hj_session_players
                    WHERE session_id = ?
                    ORDER BY joined_at''', (session_id,))
        results = c.fetchall()
        conn.close()
        return results
