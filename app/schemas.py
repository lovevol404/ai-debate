"""Pydantic schemas for AI Debate platform."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DebateStatusEnum(str, Enum):
    """Debate status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"


class MessageSideEnum(str, Enum):
    """Message side enumeration."""
    PRO = "pro"
    CON = "con"


# ============== LLM Config Schemas ==============
class LLMConfigBase(BaseModel):
    """Base schema for LLM config."""
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    base_url: str = Field(..., description="API 基础地址")
    model_name: str = Field(..., description="模型名称")
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(default=1000, ge=100, le=10000, description="最大 tokens")


class LLMConfigCreate(LLMConfigBase):
    """Schema for creating LLM config."""
    api_key: str = Field(..., description="API 密钥")


class LLMConfigUpdate(BaseModel):
    """Schema for updating LLM config."""
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_active: Optional[bool] = None


class LLMConfigResponse(LLMConfigBase):
    """Schema for LLM config response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============== Debate Topic Schemas ==============
class DebateTopicBase(BaseModel):
    """Base schema for debate topic."""
    title: str = Field(..., min_length=1, max_length=500, description="辩题标题")
    description: Optional[str] = Field(None, description="辩题描述")
    round_config: Optional[str] = Field(None, description="轮次配置 (JSON)")
    task_config: Optional[str] = Field(None, description="任务配置 (JSON)")


class DebateTopicCreate(DebateTopicBase):
    """Schema for creating debate topic."""
    pass


class DebateTopicResponse(DebateTopicBase):
    """Schema for debate topic response."""
    id: int
    created_at: datetime
    debate_count: int = 0

    class Config:
        from_attributes = True


class DebateTopicUpdate(BaseModel):
    """Schema for updating debate topic."""
    title: Optional[str] = None
    description: Optional[str] = None
    round_config: Optional[str] = None
    task_config: Optional[str] = None


# ============== Debate Message Schemas ==============
class DebateMessageBase(BaseModel):
    """Base schema for debate message."""
    side: MessageSideEnum
    content: str
    round: int
    phase: str


class DebateMessageCreate(DebateMessageBase):
    """Schema for creating debate message."""
    pass


class DebateMessageResponse(DebateMessageBase):
    """Schema for debate message response."""
    id: int
    record_id: int
    timestamp: datetime

    class Config:
        from_attributes = True


# ============== Debate Record Schemas ==============
class DebateRecordBase(BaseModel):
    """Base schema for debate record."""
    topic_id: int
    pro_config_id: int
    con_config_id: int


class DebateRecordCreate(DebateRecordBase):
    """Schema for creating debate record."""
    pass


class DebateRecordStart(BaseModel):
    """Schema for starting a debate."""
    topic_id: int
    pro_config_id: int
    con_config_id: int


class DebateRecordResponse(DebateRecordBase):
    """Schema for debate record response."""
    id: int
    status: DebateStatusEnum
    winner: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    topic: Optional[DebateTopicResponse] = None
    pro_config: Optional[LLMConfigResponse] = None
    con_config: Optional[LLMConfigResponse] = None
    messages: List[DebateMessageResponse] = []

    class Config:
        from_attributes = True


class DebateRecordListResponse(BaseModel):
    """Schema for debate record list response."""
    id: int
    status: DebateStatusEnum
    winner: Optional[str] = None
    created_at: datetime
    topic_title: str
    pro_config_name: str
    con_config_name: str

    class Config:
        from_attributes = True


# ============== Stream Event Schemas ==============
class StreamEvent(BaseModel):
    """Schema for WebSocket stream event."""
    event_type: str  # "start", "round", "message", "complete", "error"
    data: dict


class StreamMessage(BaseModel):
    """Schema for stream message."""
    side: str
    content: str
    round: int
    phase: str
