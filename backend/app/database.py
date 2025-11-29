"""
Database Configuration & Models
================================
Handles PostgreSQL connection, session management, and ORM models.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Load environment variables
load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Raja#2001@localhost:5432/pair_coding_db")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==================== DATABASE MODELS ====================

class Room(Base):
    """
    Room Model - Stores collaborative coding session data
    
    Attributes:
        room_id: Unique 8-character identifier for the room
        code: Current code content in the room
        language: Programming language (default: python)
        created_at: Timestamp when room was created
        updated_at: Timestamp of last code update
    """
    __tablename__ = "rooms"
    
    room_id = Column(String(8), primary_key=True, index=True)
    code = Column(Text, default="# Welcome! Start coding here...\n")
    language = Column(String(20), default="python")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Room(room_id={self.room_id}, language={self.language})>"


# ==================== DATABASE FUNCTIONS ====================

def init_database():
    """
    Initialize database - Create all tables if they don't exist
    Should be called on application startup
    """
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized successfully")


def get_db():
    """
    Dependency injection for database sessions
    Yields a database session and ensures proper cleanup
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db session here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== ROOM OPERATIONS ====================

def create_room(db: Session, language: str = "python") -> str:
    """
    Create a new coding room with unique ID
    
    Args:
        db: Database session
        language: Programming language for syntax highlighting
        
    Returns:
        room_id: 8-character unique room identifier
    """
    import uuid
    room_id = str(uuid.uuid4())[:8]  # Generate short unique ID
    
    new_room = Room(
        room_id=room_id,
        code="# Welcome! Start coding here...\n",
        language=language
    )
    
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    
    return room_id


def get_room(db: Session, room_id: str) -> Room:
    """
    Retrieve room by ID
    
    Args:
        db: Database session
        room_id: Room identifier
        
    Returns:
        Room object or None if not found
    """
    return db.query(Room).filter(Room.room_id == room_id).first()


def update_room_code(db: Session, room_id: str, code: str) -> bool:
    """
    Update code content in a room
    
    Args:
        db: Database session
        room_id: Room identifier
        code: New code content
        
    Returns:
        True if updated successfully, False otherwise
    """
    room = get_room(db, room_id)
    if room:
        room.code = code
        room.updated_at = datetime.utcnow()
        db.commit()
        return True
    return False
