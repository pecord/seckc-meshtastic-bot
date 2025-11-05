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
