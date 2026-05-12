"""Database module for storing user attempts and progress."""

import sqlite3
from datetime import datetime
from pathlib import Path
from src.config import DB_PATH


class Database:
    """SQLite database handler for French Evaluator."""

    def __init__(self, db_path=DB_PATH):
        """Initialize database connection."""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Attempts table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                practice_sentence TEXT NOT NULL,
                recognized_text TEXT NOT NULL,
                cefr_level TEXT NOT NULL,
                pronunciation_score REAL NOT NULL,
                fluency_score REAL NOT NULL,
                grammar_score REAL NOT NULL,
                vocabulary_score REAL NOT NULL,
                overall_score REAL NOT NULL,
                feedback TEXT,
                audio_path TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """
        )

        # Progress tracking table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                cefr_level TEXT NOT NULL,
                attempts_count INTEGER DEFAULT 0,
                average_score REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                UNIQUE(user_id, cefr_level)
            )
        """
        )

        conn.commit()
        conn.close()

    def add_user(self, username):
        """Add new user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            # User already exists, get their ID
            return self.get_user_id(username)

    def get_user_id(self, username):
        """Get user ID by username."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        return result["id"] if result else None

    def add_attempt(
        self,
        username,
        practice_sentence,
        recognized_text,
        cefr_level,
        pronunciation_score,
        fluency_score,
        grammar_score,
        vocabulary_score,
        overall_score,
        feedback,
        audio_path=None,
    ):
        """Record a practice attempt."""
        user_id = self.get_user_id(username)
        if user_id is None:
            user_id = self.add_user(username)

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO attempts (
                user_id, practice_sentence, recognized_text, cefr_level,
                pronunciation_score, fluency_score, grammar_score, vocabulary_score,
                overall_score, feedback, audio_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                user_id,
                practice_sentence,
                recognized_text,
                cefr_level,
                pronunciation_score,
                fluency_score,
                grammar_score,
                vocabulary_score,
                overall_score,
                feedback,
                audio_path,
            ),
        )
        conn.commit()
        conn.close()

    def get_user_progress(self, username):
        """Get user's progress across all CEFR levels."""
        user_id = self.get_user_id(username)
        if user_id is None:
            return []

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM progress WHERE user_id = ? ORDER BY cefr_level",
            (user_id,),
        )
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]

    def update_progress(self, username, cefr_level, score):
        """Update user progress for a CEFR level."""
        user_id = self.get_user_id(username)
        if user_id is None:
            user_id = self.add_user(username)

        conn = self.get_connection()
        cursor = conn.cursor()

        # Get current progress
        cursor.execute(
            "SELECT attempts_count, average_score FROM progress WHERE user_id = ? AND cefr_level = ?",
            (user_id, cefr_level),
        )
        result = cursor.fetchone()

        if result:
            attempts = result["attempts_count"] + 1
            avg_score = (
                result["average_score"] * result["attempts_count"] + score
            ) / attempts
            cursor.execute(
                """
                UPDATE progress 
                SET attempts_count = ?, average_score = ?, last_updated = CURRENT_TIMESTAMP
                WHERE user_id = ? AND cefr_level = ?
            """,
                (attempts, avg_score, user_id, cefr_level),
            )
        else:
            cursor.execute(
                """
                INSERT INTO progress (user_id, cefr_level, attempts_count, average_score)
                VALUES (?, ?, 1, ?)
            """,
                (user_id, cefr_level, score),
            )

        conn.commit()
        conn.close()

    def get_recent_attempts(self, username, limit=10):
        """Get user's recent attempts."""
        user_id = self.get_user_id(username)
        if user_id is None:
            return []

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM attempts 
            WHERE user_id = ? 
            ORDER BY session_date DESC 
            LIMIT ?
        """,
            (user_id, limit),
        )
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]
