"""SQLAlchemy models for AI Debate platform."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum as SQLEnum, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .database import Base


class DebateStatus(str, enum.Enum):
    """Debate status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"


class MessageSide(str, enum.Enum):
    """Message side enumeration."""
    PRO = "pro"    # 正方
    CON = "con"    # 反方


class LLMConfig(Base):
    """LLM configuration model."""
    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    base_url = Column(String(500), nullable=False)
    api_key = Column(String(500), nullable=False)
    model_name = Column(String(100), nullable=False)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    pro_debates = relationship("DebateRecord", foreign_keys="DebateRecord.pro_config_id", back_populates="pro_config")
    con_debates = relationship("DebateRecord", foreign_keys="DebateRecord.con_config_id", back_populates="con_config")


class DebateTopic(Base):
    """Debate topic model."""
    __tablename__ = "debate_topics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    round_config = Column(Text, nullable=True)  # JSON string for round configuration
    task_config = Column(Text, nullable=True)  # JSON string for task configuration
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    debates = relationship("DebateRecord", back_populates="topic", cascade="all, delete-orphan")


class DebateRecord(Base):
    """Debate record model."""
    __tablename__ = "debate_records"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("debate_topics.id"), nullable=False)
    pro_config_id = Column(Integer, ForeignKey("llm_configs.id"), nullable=False)
    con_config_id = Column(Integer, ForeignKey("llm_configs.id"), nullable=False)
    status = Column(SQLEnum(DebateStatus), default=DebateStatus.PENDING)
    winner = Column(String(10), nullable=True)  # "pro", "con", or "draw"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    topic = relationship("DebateTopic", back_populates="debates")
    pro_config = relationship("LLMConfig", foreign_keys=[pro_config_id], back_populates="pro_debates")
    con_config = relationship("LLMConfig", foreign_keys=[con_config_id], back_populates="con_debates")
    messages = relationship("DebateMessage", back_populates="record", cascade="all, delete-orphan", order_by="DebateMessage.round")


class DebateMessage(Base):
    """Debate message model."""
    __tablename__ = "debate_messages"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("debate_records.id"), nullable=False)
    side = Column(SQLEnum(MessageSide), nullable=False)
    content = Column(Text, nullable=False)
    round = Column(Integer, nullable=False)  # Round number
    phase = Column(String(50), nullable=False)  # 立论，驳论，自由辩论，总结
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    record = relationship("DebateRecord", back_populates="messages")
