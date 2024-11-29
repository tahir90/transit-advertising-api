from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Numeric, Date, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geography
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from enum import Enum
from sqlalchemy import Index

Base = declarative_base()

class Driver(Base):
    __tablename__ = "drivers"
    
    driver_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    contact_info = Column(JSONB, nullable=False)  # Make required
    vehicle_details = Column(JSONB, nullable=False)  # Make required
    registration_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='active')

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended')", 
            name='valid_driver_status'
        ),
        Index('idx_driver_status', 'status'),
        Index('idx_driver_registration', 'registration_date')
    )


class Session(Base):
    __tablename__ = "sessions"
    
    session_id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey('drivers.driver_id'))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    total_distance_km = Column(Numeric(10, 2))
    status = Column(String(20), default='active')
    completion_status = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('end_time IS NULL OR end_time > start_time', 
                       name='valid_session_timeline'),
    )

class Coordinate(Base):
    __tablename__ = "coordinates"
    
    coord_id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.session_id'))
    timestamp = Column(DateTime, nullable=False)
    location = Column(Geography(geometry_type='POINT', srid=4326))
    speed = Column(Float)
    altitude = Column(Float)
    accuracy = Column(Float)
    bearing = Column(Float)


class Brand(Base):
    __tablename__ = "brands"
    
    brand_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    contact_info = Column(JSONB)
    industry = Column(String(50))
    registered_at = Column(DateTime, default=datetime.utcnow)


class Impression(Base):
    __tablename__ = "impressions"
    
    impression_id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.campaign_id'))
    location = Column(Geography(geometry_type='POINT', srid=4326))
    timestamp = Column(DateTime)
    impression_count = Column(Integer)

class Report(Base):
    __tablename__ = "reports"
    
    report_id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.campaign_id'))
    generated_at = Column(DateTime, default=datetime.utcnow)
    metrics = Column(JSONB)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    log_id = Column(Integer, primary_key=True)
    entity_type = Column(String(50), nullable=False)  # e.g., 'driver', 'campaign'
    entity_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)  # 'create', 'update', 'delete'
    changes = Column(JSONB)  # Store the before/after values
    performed_by = Column(Integer)  # User ID who made the change
    performed_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))  # IPv6 compatible length



class CampaignStatus(str, Enum):
    DRAFT = 'draft'
    PENDING = 'pending'
    ACTIVE = 'active'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class Campaign(Base):
    __tablename__ = "campaigns"
    
    campaign_id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey('brands.brand_id'))
    name = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    budget = Column(Numeric(10, 2))
    target_audience = Column(JSONB)
    status = Column(String(20), default=CampaignStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.utcnow)
    actual_spend = Column(Numeric(10, 2), default=0)
    performance_metrics = Column(JSONB)  # Store KPIs
    
    __table_args__ = (
        CheckConstraint('end_date >= start_date', name='valid_campaign_dates'),
        CheckConstraint('actual_spend <= budget', name='budget_limit'),
    )


class ArchivedSession(Base):
    __tablename__ = "archived_sessions"
    session_id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey('drivers.driver_id'))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    total_distance_km = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    archived_at = Column(DateTime, default=datetime.utcnow)

class ArchivedCoordinate(Base):
    __tablename__ = "archived_coordinates"
    coord_id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.session_id'))
    timestamp = Column(DateTime, nullable=False)
    location = Column(Geography(geometry_type='POINT', srid=4326))
    speed = Column(Float)
    altitude = Column(Float)
    bearing = Column(Float)
    accuracy = Column(Float)
    archived_at = Column(DateTime, default=datetime.utcnow)


class POI(Base):
    __tablename__ = "pois"
    
    poi_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50))
    location = Column(Geography(geometry_type='POINT', srid=4326))
    footfall_estimate = Column(Integer)
    peak_hours = Column(JSONB)  # Store hourly footfall patterns
    demographic_data = Column(JSONB)  # Store demographic information
    operational_hours = Column(JSONB)  # Store opening hours
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


__table_args__ = (
    Index('idx_coordinates_session_time', 'session_id', 'timestamp'),
    Index('idx_campaign_status_dates', 'status', 'start_date', 'end_date'),
    Index('idx_poi_location', 'location', postgresql_using='gist'),
    Index('idx_impressions_campaign_time', 'campaign_id', 'timestamp')
)


class BillingRecord(Base):
    __tablename__ = "billing_records"
    
    billing_id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.campaign_id'))
    brand_id = Column(Integer, ForeignKey('brands.brand_id'))
    amount = Column(Numeric(10, 2))
    billing_date = Column(Date, nullable=False)
    payment_status = Column(String(20), default='pending')
    payment_date = Column(DateTime)
    invoice_number = Column(String(50), unique=True)