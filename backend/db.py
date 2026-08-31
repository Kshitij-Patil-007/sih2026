"""
SQLite Database for Session Management
Stores uploaded images, queries, and results for the FastAPI backend
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

# Database location
DB_PATH = Path(__file__).parent.parent / "sih_sessions.db"


def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Sessions table - stores uploaded images
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            image_count INTEGER NOT NULL
        )
    """)

    # Images table - stores image metadata
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            image_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            modality TEXT,
            format TEXT,
            width INTEGER,
            height INTEGER,
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    """)

    # Queries table - stores user queries and results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            query_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            task_type TEXT NOT NULL,
            answer TEXT,
            confidence REAL,
            visual_evidence TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    """)

    # Audit trail table - explicitly required by judges
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            task TEXT,
            model_used TEXT,
            parameters TEXT,
            details TEXT,
            FOREIGN KEY (query_id) REFERENCES queries (query_id)
        )
    """)

    conn.commit()
    conn.close()


def create_session(image_count: int) -> str:
    """Create a new session"""
    session_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sessions (session_id, created_at, image_count)
        VALUES (?, ?, ?)
    """, (session_id, datetime.utcnow().isoformat(), image_count))

    conn.commit()
    conn.close()
    return session_id


def add_image(session_id: str, filename: str, filepath: str, modality: Optional[str],
              format: str, width: int, height: int) -> str:
    """Add an image to a session"""
    image_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO images (image_id, session_id, filename, filepath, modality,
                           format, width, height, uploaded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (image_id, session_id, filename, filepath, modality, format, width, height,
          datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()
    return image_id


def get_session_images(session_id: str) -> List[Dict]:
    """Get all images for a session"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT image_id, filename, filepath, modality, format, width, height
        FROM images WHERE session_id = ?
    """, (session_id,))

    images = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return images


def create_query(session_id: str, query_text: str, task_type: str) -> str:
    """Create a new query record"""
    query_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO queries (query_id, session_id, query_text, task_type, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (query_id, session_id, query_text, task_type, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()
    return query_id


def update_query_result(query_id: str, answer: str, confidence: Optional[float],
                        visual_evidence: Optional[Dict]):
    """Update query with result"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE queries
        SET answer = ?, confidence = ?, visual_evidence = ?, completed_at = ?
        WHERE query_id = ?
    """, (answer, confidence, json.dumps(visual_evidence) if visual_evidence else None,
          datetime.utcnow().isoformat(), query_id))

    conn.commit()
    conn.close()


def get_query_result(query_id: str) -> Optional[Dict]:
    """Get query result by ID"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT query_id, session_id, query_text, task_type, answer,
               confidence, visual_evidence, created_at, completed_at
        FROM queries WHERE query_id = ?
    """, (query_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        result = dict(row)
        if result['visual_evidence']:
            result['visual_evidence'] = json.loads(result['visual_evidence'])
        return result
    return None


def session_exists(session_id: str) -> bool:
    """Check if session exists"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM sessions WHERE session_id = ?", (session_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


# Initialize database on import
init_db()
