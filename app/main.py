from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text  # Add this import
from .db import get_db
from .core.config import settings
from .api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Transit Advertising API"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Use text() to properly format the SQL query
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)