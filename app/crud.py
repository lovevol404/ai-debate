"""CRUD operations for AI Debate platform."""
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional

from . import models, schemas


# ============== LLM Config CRUD ==============
def get_llm_config(db: Session, config_id: int) -> Optional[models.LLMConfig]:
    """Get LLM config by ID."""
    return db.query(models.LLMConfig).filter(models.LLMConfig.id == config_id).first()


def get_llm_configs(db: Session, skip: int = 0, limit: int = 100) -> List[models.LLMConfig]:
    """Get all LLM configs."""
    return db.query(models.LLMConfig).offset(skip).limit(limit).all()


def get_active_llm_configs(db: Session) -> List[models.LLMConfig]:
    """Get all active LLM configs."""
    return db.query(models.LLMConfig).filter(models.LLMConfig.is_active == True).all()


def create_llm_config(db: Session, config: schemas.LLMConfigCreate) -> models.LLMConfig:
    """Create a new LLM config."""
    db_config = models.LLMConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


def update_llm_config(db: Session, config_id: int, config: schemas.LLMConfigUpdate) -> Optional[models.LLMConfig]:
    """Update LLM config."""
    db_config = get_llm_config(db, config_id)
    if not db_config:
        return None

    update_data = config.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)

    db.commit()
    db.refresh(db_config)
    return db_config


def delete_llm_config(db: Session, config_id: int) -> bool:
    """Delete LLM config."""
    db_config = get_llm_config(db, config_id)
    if not db_config:
        return False

    db.delete(db_config)
    db.commit()
    return True


# ============== Debate Topic CRUD ==============
def get_debate_topic(db: Session, topic_id: int) -> Optional[models.DebateTopic]:
    """Get debate topic by ID."""
    return db.query(models.DebateTopic).filter(models.DebateTopic.id == topic_id).first()


def get_debate_topics(db: Session, skip: int = 0, limit: int = 100) -> List[models.DebateTopic]:
    """Get all debate topics."""
    return db.query(models.DebateTopic).order_by(models.DebateTopic.created_at.desc()).offset(skip).limit(limit).all()


def create_debate_topic(db: Session, topic: schemas.DebateTopicCreate) -> models.DebateTopic:
    """Create a new debate topic."""
    db_topic = models.DebateTopic(**topic.model_dump())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic


def update_debate_topic(db: Session, topic_id: int, topic: schemas.DebateTopicUpdate) -> Optional[models.DebateTopic]:
    """Update debate topic."""
    db_topic = get_debate_topic(db, topic_id)
    if not db_topic:
        return None

    update_data = topic.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_topic, field, value)

    db.commit()
    db.refresh(db_topic)
    return db_topic


def delete_debate_topic(db: Session, topic_id: int) -> bool:
    """Delete debate topic."""
    db_topic = get_debate_topic(db, topic_id)
    if not db_topic:
        return False

    db.delete(db_topic)
    db.commit()
    return True


# ============== Debate Record CRUD ==============
def get_debate_record(db: Session, record_id: int) -> Optional[models.DebateRecord]:
    """Get debate record by ID."""
    record = db.query(models.DebateRecord).filter(models.DebateRecord.id == record_id).first()
    if record:
        # Preload messages
        db.refresh(record)
    return record


def get_debate_records(db: Session, skip: int = 0, limit: int = 100) -> List[models.DebateRecord]:
    """Get all debate records."""
    return (
        db.query(models.DebateRecord)
        .order_by(models.DebateRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_debate_record(db: Session, record: schemas.DebateRecordCreate) -> models.DebateRecord:
    """Create a new debate record."""
    db_record = models.DebateRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


def update_debate_record_status(
    db: Session,
    record_id: int,
    status: models.DebateStatus
) -> Optional[models.DebateRecord]:
    """Update debate record status."""
    db_record = get_debate_record(db, record_id)
    if not db_record:
        return None

    db_record.status = status
    if status == models.DebateStatus.COMPLETED:
        from sqlalchemy.sql import func
        db_record.completed_at = func.now()

    db.commit()
    db.refresh(db_record)
    return db_record


def update_debate_record_winner(
    db: Session,
    record_id: int,
    winner: str
) -> Optional[models.DebateRecord]:
    """Update debate record winner."""
    db_record = get_debate_record(db, record_id)
    if not db_record:
        return None

    db_record.winner = winner
    db_record.status = models.DebateStatus.COMPLETED
    from sqlalchemy.sql import func
    db_record.completed_at = func.now()

    db.commit()
    db.refresh(db_record)
    return db_record


# ============== Debate Message CRUD ==============
def create_debate_message(
    db: Session,
    record_id: int,
    side: models.MessageSide,
    content: str,
    round: int,
    phase: str
) -> models.DebateMessage:
    """Create a new debate message."""
    db_message = models.DebateMessage(
        record_id=record_id,
        side=side,
        content=content,
        round=round,
        phase=phase
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_debate_messages(db: Session, record_id: int) -> List[models.DebateMessage]:
    """Get all messages for a debate record."""
    return (
        db.query(models.DebateMessage)
        .filter(models.DebateMessage.record_id == record_id)
        .order_by(models.DebateMessage.round, models.DebateMessage.timestamp)
        .all()
    )
