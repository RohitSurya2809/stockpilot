"""
Database connection and session management for StockPilot.
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from config import get_database_url

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = get_database_url()

# Create SQLAlchemy engine
# For PostgreSQL in production
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=10,
    echo=False  # Set to True for SQL query logging during debug
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Usage in FastAPI:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables.

    This should be called when setting up the application.
    """
    try:
        # Import all models here to ensure they are registered with Base
        from models import sku, inventory, sales_history, supplier, purchase_order, forecast, agent_log, knowledge_base

        # Create all tables
        Base.metadata.create_all(bind=engine)

        logger.info("✓ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}")
        return False


def drop_all_tables():
    """
    Drop all tables - USE WITH CAUTION!

    Only for development/testing purposes.
    """
    Base.metadata.drop_all(bind=engine)
    logger.warning("⚠ All tables dropped")


def test_connection():
    """
    Test database connection.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)

    print("Testing database connection...")
    if test_connection():
        print("✓ Connection successful")

        print("\nInitializing database...")
        if init_db():
            print("✓ Database initialized")
        else:
            print("✗ Database initialization failed")
    else:
        print("✗ Connection failed")
