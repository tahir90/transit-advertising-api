from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from .... import schemas, models
from ....db import get_db
from datetime import datetime

router = APIRouter()

@router.post("/start", response_model=schemas.SessionResponse)
async def start_session(
    session: schemas.SessionCreate,
    db: Session = Depends(get_db)
):
    # Check if driver exists
    driver = db.query(models.Driver).filter(models.Driver.driver_id == session.driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with id {session.driver_id} not found"
        )
    
    # Check if driver already has an active session
    active_session = db.query(models.Session).filter(
        models.Session.driver_id == session.driver_id,
        models.Session.status == "active"
    ).first()
    
    if active_session:
        return active_session

    # Create new session with server time
    db_session = models.Session(
        driver_id=session.driver_id,
        start_time=datetime.utcnow(),  # Use server time
        status="active"
    )
    
    try:
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{session_id}/end", response_model=schemas.SessionResponse)
async def end_session(
    session_id: int,
    session_update: schemas.SessionUpdate,
    db: Session = Depends(get_db)
):
    # Get active session
    db_session = db.query(models.Session).filter(
        models.Session.session_id == session_id,
        models.Session.status == "active"
    ).first()
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active session with id {session_id} not found"
        )

    # Update session with server time
    db_session.end_time = datetime.utcnow()  # Use server time
    db_session.total_distance_km = session_update.total_distance_km
    db_session.status = "completed"
    
    try:
        db.commit()
        db.refresh(db_session)
        return db_session
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/driver/{driver_id}", response_model=List[schemas.SessionResponse])
async def get_driver_sessions(
    driver_id: int,
    status: Optional[str] = None,  # Optional status filter
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # Build query
    query = db.query(models.Session).filter(models.Session.driver_id == driver_id)
    
    # Apply status filter if provided
    if status:
        if status not in ["active", "completed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status must be either 'active' or 'completed'"
            )
        query = query.filter(models.Session.status == status)
    
    # Get results
    sessions = query.order_by(models.Session.start_time.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return sessions