"""
Database configuration and session management for AlphaPulse.

This module provides database connection pooling, session management,
and Decimal type handling for SQLAlchemy.
"""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alphapulse"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,  # Number of connections to keep open
    max_overflow=10,  # Number of connections to create beyond pool_size
    pool_timeout=30,  # Seconds to wait for a connection from pool
    pool_recycle=1800,  # Recycle connections after 30 minutes
    echo=False,  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Yields:
        Session: SQLAlchemy database session

    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database by creating all tables.

    This should be called during application startup or
    as part of database migration scripts.
    """
    # Import models to ensure they are registered with Base
    from src.alphapulse.api.models import Price, TechnicalIndicator, TradingSignal

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


def drop_db():
    """
    Drop all database tables.

    Warning: This will delete all data!
    Only use for development/testing.
    """
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped successfully")


# Decimal type handling for SQLAlchemy
# SQLAlchemy's DECIMAL type already handles Python Decimal objects correctly
# No additional configuration needed for basic Decimal support

# For advanced Decimal handling (e.g., custom marshalling), we could add:
# from sqlalchemy import TypeDecorator
# from decimal import Decimal
#
# class SqlDecimal(TypeDecorator):
#     """Custom Decimal type with specific precision handling."""
#     impl = DECIMAL
#
#     def process_bind_param(self, value, dialect):
#         if value is not None:
#             if not isinstance(value, Decimal):
#                 value = Decimal(str(value))
#             # Ensure proper precision
#             value = value.quantize(Decimal('0.00000001'))
#         return value
#
#     def process_result_value(self, value, dialect):
#         if value is not None:
#             if not isinstance(value, Decimal):
#                 value = Decimal(str(value))
#         return value
