from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from .... import schemas, models
from ....db import get_db
from geoalchemy2 import functions as geo_func
from sqlalchemy import func
from shapely.geometry import Point
from geoalchemy2.shape import from_shape

router = APIRouter()

@router.post("/", response_model=schemas.CoordinateResponse)
async def create_coordinate(
    coordinate: schemas.CoordinateCreate,
    db: Session = Depends(get_db)
):
    # Check if session exists and is active
    session = db.query(models.Session).filter(
        models.Session.session_id == coordinate.session_id,
        models.Session.status == "active"
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active session not found"
        )

    # Create Point geometry from latitude and longitude
    point = Point(coordinate.longitude, coordinate.latitude)
    
    # Create coordinate record
    db_coordinate = models.Coordinate(
        session_id=coordinate.session_id,
        timestamp=datetime.utcnow(),
        location=from_shape(point, srid=4326),
        speed=coordinate.speed,
        altitude=coordinate.altitude,
        bearing=coordinate.bearing,
        accuracy=coordinate.accuracy
    )
    
    try:
        db.add(db_coordinate)
        db.commit()
        db.refresh(db_coordinate)
        
        # Convert for response
        return {
            "coord_id": db_coordinate.coord_id,
            "session_id": db_coordinate.session_id,
            "timestamp": db_coordinate.timestamp,
            "latitude": coordinate.latitude,
            "longitude": coordinate.longitude,
            "speed": db_coordinate.speed,
            "altitude": db_coordinate.altitude,
            "bearing": db_coordinate.bearing,
            "accuracy": db_coordinate.accuracy
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/session/{session_id}", response_model=List[schemas.CoordinateResponse])
async def get_session_coordinates(
    session_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # Query with ST_AsText to get WKT representation
    coordinates = db.query(
        models.Coordinate.coord_id,
        models.Coordinate.session_id,
        models.Coordinate.timestamp,
        func.ST_AsText(models.Coordinate.location).label('location_text'),
        models.Coordinate.speed,
        models.Coordinate.altitude,
        models.Coordinate.bearing,
        models.Coordinate.accuracy
    ).filter(
        models.Coordinate.session_id == session_id
    ).order_by(
        models.Coordinate.timestamp
    ).offset(skip).limit(limit).all()
    
    # Parse WKT to get coordinates
    result = []
    for coord in coordinates:
        # Parse POINT(longitude latitude) format
        if coord.location_text:
            point_text = coord.location_text.replace('POINT(', '').replace(')', '')
            lon, lat = map(float, point_text.split())
            result.append({
                "coord_id": coord.coord_id,
                "session_id": coord.session_id,
                "timestamp": coord.timestamp,
                "latitude": lat,
                "longitude": lon,
                "speed": coord.speed,
                "altitude": coord.altitude,
                "bearing": coord.bearing,
                "accuracy": coord.accuracy
            })
    
    return result


@router.post("/batch", response_model=List[schemas.CoordinateResponse])
async def create_coordinates_batch(
    coordinates: List[schemas.CoordinateCreate],
    db: Session = Depends(get_db)
):
    if not coordinates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty coordinate list"
        )
    
    # Validate all coordinates belong to same session
    session_ids = set(coord.session_id for coord in coordinates)
    if len(session_ids) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All coordinates must belong to same session"
        )
    
    session_id = coordinates[0].session_id
    
    # Check if session exists and is active
    session = db.query(models.Session).filter(
        models.Session.session_id == session_id,
        models.Session.status == "active"
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active session not found"
        )

    response_coordinates = []
    try:
        for coordinate in coordinates:
            point = Point(coordinate.longitude, coordinate.latitude)
            db_coordinate = models.Coordinate(
                session_id=session_id,
                timestamp=datetime.utcnow(),
                location=from_shape(point, srid=4326),
                speed=coordinate.speed,
                altitude=coordinate.altitude,
                bearing=coordinate.bearing,
                accuracy=coordinate.accuracy
            )
            db.add(db_coordinate)
            db.flush()  # This will assign coord_id
            
            # Create response object
            response_coordinates.append({
                "coord_id": db_coordinate.coord_id,
                "session_id": db_coordinate.session_id,
                "timestamp": db_coordinate.timestamp,
                "latitude": coordinate.latitude,
                "longitude": coordinate.longitude,
                "speed": db_coordinate.speed,
                "altitude": db_coordinate.altitude,
                "bearing": db_coordinate.bearing,
                "accuracy": db_coordinate.accuracy
            })
        
        db.commit()
        return response_coordinates
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )