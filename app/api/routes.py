"""API routes for AI Debate platform."""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import asyncio
import json

from .. import crud, schemas, models
from ..database import get_db
from ..debate.engine import get_or_create_engine, remove_engine

router = APIRouter()


# ============== LLM Config Routes ==============
@router.get("/llm-configs", response_model=List[schemas.LLMConfigResponse], tags=["LLM Config"])
def list_llm_configs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all LLM configurations."""
    return crud.get_llm_configs(db, skip, limit)


@router.get("/llm-configs/active", response_model=List[schemas.LLMConfigResponse], tags=["LLM Config"])
def list_active_llm_configs(db: Session = Depends(get_db)):
    """Get all active LLM configurations."""
    return crud.get_active_llm_configs(db)


@router.get("/llm-configs/{config_id}", response_model=schemas.LLMConfigResponse, tags=["LLM Config"])
def get_llm_config(config_id: int, db: Session = Depends(get_db)):
    """Get a specific LLM configuration."""
    config = crud.get_llm_config(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="LLM config not found")
    return config


@router.post("/llm-configs", response_model=schemas.LLMConfigResponse, tags=["LLM Config"])
def create_llm_config(config: schemas.LLMConfigCreate, db: Session = Depends(get_db)):
    """Create a new LLM configuration."""
    return crud.create_llm_config(db, config)


@router.put("/llm-configs/{config_id}", response_model=schemas.LLMConfigResponse, tags=["LLM Config"])
def update_llm_config(config_id: int, config: schemas.LLMConfigUpdate, db: Session = Depends(get_db)):
    """Update an LLM configuration."""
    updated = crud.update_llm_config(db, config_id, config)
    if not updated:
        raise HTTPException(status_code=404, detail="LLM config not found")
    return updated


@router.delete("/llm-configs/{config_id}", tags=["LLM Config"])
def delete_llm_config(config_id: int, db: Session = Depends(get_db)):
    """Delete an LLM configuration."""
    if not crud.delete_llm_config(db, config_id):
        raise HTTPException(status_code=404, detail="LLM config not found")
    return {"message": "Deleted successfully"}


# ============== Debate Topic Routes ==============
@router.get("/topics", response_model=List[schemas.DebateTopicResponse], tags=["Debate Topic"])
def list_topics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all debate topics."""
    topics = crud.get_debate_topics(db, skip, limit)
    # Add debate count
    result = []
    for topic in topics:
        topic_dict = schemas.DebateTopicResponse.model_validate(topic)
        topic_dict.debate_count = len(topic.debates)
        result.append(topic_dict)
    return result


@router.get("/topics/{topic_id}", response_model=schemas.DebateTopicResponse, tags=["Debate Topic"])
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    """Get a specific debate topic."""
    topic = crud.get_debate_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.post("/topics", response_model=schemas.DebateTopicResponse, tags=["Debate Topic"])
def create_topic(topic: schemas.DebateTopicCreate, db: Session = Depends(get_db)):
    """Create a new debate topic."""
    return crud.create_debate_topic(db, topic)


@router.put("/topics/{topic_id}", response_model=schemas.DebateTopicResponse, tags=["Debate Topic"])
def update_topic(topic_id: int, topic: schemas.DebateTopicUpdate, db: Session = Depends(get_db)):
    """Update a debate topic."""
    updated = crud.update_debate_topic(db, topic_id, topic)
    if not updated:
        raise HTTPException(status_code=404, detail="Topic not found")
    return updated


@router.delete("/topics/{topic_id}", tags=["Debate Topic"])
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    """Delete a debate topic."""
    if not crud.delete_debate_topic(db, topic_id):
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"message": "Deleted successfully"}


# ============== Debate Record Routes ==============
@router.get("/debates", response_model=List[schemas.DebateRecordListResponse], tags=["Debate Record"])
def list_debates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all debate records."""
    records = crud.get_debate_records(db, skip, limit)
    result = []
    for record in records:
        result.append({
            "id": record.id,
            "status": record.status.value,
            "winner": record.winner,
            "created_at": record.created_at,
            "topic_title": record.topic.title if record.topic else "Unknown",
            "pro_config_name": record.pro_config.name if record.pro_config else "Unknown",
            "con_config_name": record.con_config.name if record.con_config else "Unknown",
        })
    return result


@router.get("/debates/{debate_id}", response_model=schemas.DebateRecordResponse, tags=["Debate Record"])
def get_debate(debate_id: int, db: Session = Depends(get_db)):
    """Get a specific debate record with details."""
    record = crud.get_debate_record(db, debate_id)
    if not record:
        raise HTTPException(status_code=404, detail="Debate record not found")
    return record


@router.post("/debates/start", response_model=schemas.DebateRecordResponse, tags=["Debate Record"])
def start_debate(request: schemas.DebateRecordStart, db: Session = Depends(get_db)):
    """Start a new debate."""
    # Validate topic and configs exist
    topic = crud.get_debate_topic(db, request.topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    pro_config = crud.get_llm_config(db, request.pro_config_id)
    con_config = crud.get_llm_config(db, request.con_config_id)
    if not pro_config or not con_config:
        raise HTTPException(status_code=404, detail="Invalid LLM configuration")

    # Create debate record
    record = crud.create_debate_record(
        db,
        schemas.DebateRecordCreate(
            topic_id=request.topic_id,
            pro_config_id=request.pro_config_id,
            con_config_id=request.con_config_id,
        )
    )

    return record


@router.delete("/debates/{debate_id}", tags=["Debate Record"])
def delete_debate(debate_id: int, db: Session = Depends(get_db)):
    """Delete a debate record."""
    record = crud.get_debate_record(db, debate_id)
    if not record:
        raise HTTPException(status_code=404, detail="Debate record not found")

    db.delete(record)
    db.commit()
    return {"message": "Deleted successfully"}


# ============== WebSocket Streaming ==============
@router.websocket("/debates/{debate_id}/stream")
async def debate_stream(websocket: WebSocket, debate_id: int, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time debate streaming."""
    await websocket.accept()

    # Verify debate exists
    record = crud.get_debate_record(db, debate_id)
    if not record:
        await websocket.send_json({"error": "Debate not found"})
        await websocket.close()
        return

    engine = get_or_create_engine(db, debate_id)

    async def stream_callback(event: dict):
        """Send events to WebSocket client."""
        try:
            await websocket.send_json(event)
        except Exception:
            pass

    try:
        # Send acknowledgment
        await websocket.send_json({
            "event_type": "connected",
            "data": {"debate_id": debate_id}
        })

        # Run debate
        await engine.run_debate(debate_id, stream_callback)

    except WebSocketDisconnect:
        engine.abort_debate(debate_id)
        remove_engine(debate_id)
    except Exception as e:
        await websocket.send_json({
            "event_type": "error",
            "data": {"error": str(e)}
        })
        engine.abort_debate(debate_id)
        remove_engine(debate_id)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# ============== Debate Control Routes ==============
@router.post("/debates/{debate_id}/abort", tags=["Debate Record"])
def abort_debate(debate_id: int, db: Session = Depends(get_db)):
    """Abort a running debate."""
    record = crud.get_debate_record(db, debate_id)
    if not record:
        raise HTTPException(status_code=404, detail="Debate record not found")

    if record.status != models.DebateStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Debate is not in progress")

    engine = get_or_create_engine(db, debate_id)
    engine.abort_debate(debate_id)
    remove_engine(debate_id)

    crud.update_debate_record_status(db, debate_id, models.DebateStatus.ERROR)

    return {"message": "Debate aborted"}
