# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Azure PostgreSQL Database URL from environment variables
# Format: postgresql://username:password@host:port/database_name?sslmode=require
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dbadmin:admin%40123@insurance-ai-postgres-dev.postgres.database.azure.com:5432/postgres?sslmode=require"
)

# Create engine with connection pooling for Azure PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using (important for Azure)
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=True  # Set to True for SQL query logging (temporary for debugging)
)
# NOTE: For debugging database writes you can temporarily set echo=True above

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
