from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .... import schemas
from .... import models
from ....db import get_db
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict  # Add List here
import re

router = APIRouter()

@router.post("/", response_model=schemas.DriverResponse, status_code=status.HTTP_201_CREATED)
def create_driver(driver: schemas.DriverCreate, db: Session = Depends(get_db)):
    try:
        # Check if driver with same phone number exists
        existing_driver = db.query(models.Driver).filter(
            models.Driver.contact_info['phone'].astext == driver.contact_info.phone
        ).first()
        
        if existing_driver:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Driver with this phone number already exists"
            )
        
        # Convert Pydantic models to dictionaries
        contact_info_dict = driver.contact_info.model_dump()
        vehicle_details_dict = driver.vehicle_details.model_dump()
        
        # Create new driver
        db_driver = models.Driver(
            name=driver.name,
            contact_info=contact_info_dict,
            vehicle_details=vehicle_details_dict,
            status='active',
            registration_date=datetime.utcnow()
        )
        db.add(db_driver)
        db.commit()
        db.refresh(db_driver)
        
        return db_driver

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )



@router.get("/", response_model=schemas.PaginatedDriverResponse)
def get_drivers(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(models.Driver)
        
        if status:
            query = query.filter(models.Driver.status == status)
        
        total = query.count()
        drivers = query.offset(skip).limit(limit).all()
        
        # Convert SQLAlchemy models to valid Pydantic-compatible dictionaries
        driver_list = []
        for driver in drivers:
            # Ensure contact_info has all required fields
            contact_info = driver.contact_info or {}
            contact_info = {
                "phone": contact_info.get("phone", ""),
                "email": contact_info.get("email", "user@example.com"),
                "address": contact_info.get("address", "Address not provided"),
                "emergency_contact": contact_info.get("emergency_contact")
            }

            # Ensure vehicle_details has all required fields
            vehicle_details = driver.vehicle_details or {}
            vehicle_details = {
                "type": vehicle_details.get("type", ""),
                "make": vehicle_details.get("make", ""),
                "model": vehicle_details.get("model", ""),
                "year": vehicle_details.get("year", 2000),
                "plate_number": vehicle_details.get("plate_number", "") or vehicle_details.get("plate", ""),
                "color": vehicle_details.get("color")
            }

            driver_dict = {
                "driver_id": driver.driver_id,
                "name": driver.name,
                "contact_info": contact_info,
                "vehicle_details": vehicle_details,
                "status": driver.status,
                "registration_date": driver.registration_date
            }
            driver_list.append(driver_dict)

        return {
            "total": total,
            "items": driver_list,
            "page": (skip // limit) + 1,
            "pages": (total + limit - 1) // limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving drivers: {str(e)}"
        )
    
@router.put("/{driver_id}", response_model=schemas.DriverResponse)
def update_driver(
    driver_id: int, 
    driver_update: schemas.DriverCreate, 
    db: Session = Depends(get_db)
):
    try:
        db_driver = db.query(models.Driver).filter(models.Driver.driver_id == driver_id).first()
        if not db_driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Driver with ID {driver_id} not found"
            )
        
        # Check if updating phone number to one that already exists
        if driver_update.contact_info.phone != db_driver.contact_info['phone']:
            existing_driver = db.query(models.Driver).filter(
                models.Driver.contact_info['phone'].astext == driver_update.contact_info.phone,
                models.Driver.driver_id != driver_id
            ).first()
            if existing_driver:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number already registered with another driver"
                )

        # Update fields
        db_driver.name = driver_update.name
        db_driver.contact_info = driver_update.contact_info.model_dump()
        db_driver.vehicle_details = driver_update.vehicle_details.model_dump()
        
        db.commit()
        db.refresh(db_driver)
        return db_driver

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


class DriverStatus(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'

@router.patch("/{driver_id}/status", response_model=schemas.DriverResponse)
def update_driver_status(
    driver_id: int,
    status: DriverStatus,
    db: Session = Depends(get_db)
):
    db_driver = db.query(models.Driver).filter(models.Driver.driver_id == driver_id).first()
    if not db_driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with ID {driver_id} not found"
        )
    
    db_driver.status = status
    db.commit()
    db.refresh(db_driver)
    return db_driver

@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    db_driver = db.query(models.Driver).filter(models.Driver.driver_id == driver_id).first()
    if not db_driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with ID {driver_id} not found"
        )
    
    # Soft delete - just update status to 'inactive'
    db_driver.status = 'inactive'
    db.commit()
    return {"message": f"Driver {driver_id} has been deactivated"}