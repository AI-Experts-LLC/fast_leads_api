"""
Database models for API logging.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from app.database import Base

class APILog(Base):
    """
    Model for storing API request/response logs.
    """
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    method = Column(String(10), nullable=False)  # GET, POST, etc.
    endpoint = Column(String(500), nullable=False, index=True)
    request_body = Column(Text, nullable=True)  # JSON string
    response_body = Column(Text, nullable=True)  # JSON string
    status_code = Column(Integer, nullable=True)
    duration_ms = Column(Float, nullable=True)  # Request duration in milliseconds
    client_ip = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<APILog(id={self.id}, method={self.method}, endpoint={self.endpoint}, status={self.status_code})>"
