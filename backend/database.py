from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/deviceauth")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ActiveSession(Base):
    """
    Database model for tracking active user sessions across devices.
    Implements device fingerprinting and multi-device session management.
    """
    __tablename__ = "active_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # Auth0 user ID
    device_id = Column(String, unique=True, nullable=False)  # Generated device fingerprint
    user_agent = Column(Text, nullable=False)  # Browser/device user agent
    ip_address = Column(String, nullable=False)  # Client IP address
    login_time = Column(DateTime, default=datetime.utcnow)  # Initial login timestamp
    last_active = Column(DateTime, default=datetime.utcnow)  # Last activity timestamp
    
    def to_dict(self):
        """Convert session object to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "device_id": self.device_id,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "login_time": self.login_time.isoformat() if self.login_time else None,
            "last_active": self.last_active.isoformat() if self.last_active else None,
        }

def get_db():
    """
    Dependency function to get database session for FastAPI endpoints.
    Ensures proper session cleanup after each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
def create_tables():
    """Create all database tables if they don't exist"""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")