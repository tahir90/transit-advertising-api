from pydantic import BaseModel, EmailStr, constr, validator, confloat
from typing import List, Optional
from datetime import datetime
import re

# ... (Driver Schemas)

class VehicleDetails(BaseModel):
    type: constr(strip_whitespace=True, min_length=2, max_length=50)
    make: constr(strip_whitespace=True, min_length=2, max_length=50)
    model: constr(strip_whitespace=True, min_length=2, max_length=50)
    year: int
    plate_number: constr(strip_whitespace=True, min_length=5, max_length=20)
    color: Optional[str] = None

class ContactInfo(BaseModel):
    phone: constr(strip_whitespace=True, min_length=8, max_length=15)
    email: EmailStr
    address: constr(strip_whitespace=True, min_length=5, max_length=200)
    emergency_contact: Optional[str] = None

    @validator('phone')
    def validate_phone(cls, v):
        pattern = r'^\+?[1-9]\d{9,14}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid phone number format')
        return v

class DriverBase(BaseModel):
    name: constr(strip_whitespace=True, min_length=2, max_length=100)
    contact_info: ContactInfo
    vehicle_details: VehicleDetails

class DriverCreate(DriverBase):
    pass

class DriverResponse(DriverBase):
    driver_id: int
    status: str
    registration_date: datetime

    class Config:
        from_attributes = True

class PaginatedDriverResponse(BaseModel):
    total: int
    items: List[DriverResponse]
    page: int
    pages: int

    class Config:
        from_attributes = True



# ... (Session Schemas)

from pydantic import BaseModel, confloat
from typing import Optional, Literal
from datetime import datetime

# Remove start_time from SessionCreate
class SessionCreate(BaseModel):
    driver_id: int

# Remove end_time from SessionUpdate
class SessionUpdate(BaseModel):
    total_distance_km: confloat(ge=0)

class SessionResponse(BaseModel):
    session_id: int
    driver_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    total_distance_km: Optional[float] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# ... (Coordinates Schemas)

class CoordinateCreate(BaseModel):
    session_id: int
    latitude: confloat(ge=-90, le=90)  # Latitude must be between -90 and 90
    longitude: confloat(ge=-180, le=180)  # Longitude must be between -180 and 180
    speed: confloat(ge=0)  # Speed must be non-negative
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    bearing: Optional[float] = None

class CoordinateResponse(BaseModel):
    coord_id: int
    session_id: int
    timestamp: datetime
    latitude: float
    longitude: float
    speed: float
    altitude: Optional[float]
    accuracy: Optional[float]
    bearing: Optional[float]

    class Config:
        from_attributes = True
