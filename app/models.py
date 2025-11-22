"""
Database models for API logging and pending Salesforce updates.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

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


class UpdateStatus(str, enum.Enum):
    """Enum for pending update status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RecordType(str, enum.Enum):
    """Enum for Salesforce record types."""
    ACCOUNT = "ACCOUNT"  # Database uses uppercase
    CONTACT = "CONTACT"  # Database uses uppercase
    LEAD = "LEAD"  # Database uses uppercase


class PendingUpdate(Base):
    """
    Model for storing pending Salesforce updates that require approval.
    """
    __tablename__ = "pending_updates"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    status = Column(Enum(UpdateStatus), default=UpdateStatus.PENDING, nullable=False, index=True)

    # Salesforce record information
    record_type = Column(Enum(RecordType), nullable=False, index=True)
    record_id = Column(String(18), nullable=False, index=True)  # Salesforce 18-char ID
    record_name = Column(String(255), nullable=True)  # For display purposes

    # Update details
    field_updates = Column(JSON, nullable=False)  # JSON object of field: value pairs
    enrichment_type = Column(String(100), nullable=True)  # e.g., "web_search_account", "credit_enrichment"

    # Approval tracking
    approved_by = Column(String(255), nullable=True)  # User who approved
    approved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<PendingUpdate(id={self.id}, record_type={self.record_type}, record_id={self.record_id}, status={self.status})>"
