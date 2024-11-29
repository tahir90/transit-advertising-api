from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .core.config import settings
import urllib.parse

# Encode password to handle special characters
encoded_password = urllib.parse.quote_plus(settings.POSTGRES_PASSWORD)

# Construct Database URL with encoded password
DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{encoded_password}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

# Create engine with proper SSL and authentication settings for Supabase
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "sslmode": "require",
        "application_name": "transit_api",
        # Explicitly set authentication method
        "client_encoding": "utf8",
        "gssencmode": "disable",  # Disable GSSAPI authentication
    },
    pool_size=5,
    max_overflow=10,
    echo=True  # This will log SQL statements, helpful for debugging
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to use in FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()