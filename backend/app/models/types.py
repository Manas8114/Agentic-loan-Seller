"""
Portable SQLAlchemy Type Definitions

Provides cross-database compatible types that work with both PostgreSQL and SQLite.
"""

from typing import Any
import json
import uuid

from sqlalchemy import String, Text, TypeDecorator
from sqlalchemy.dialects import postgresql

from app.config import settings


def is_sqlite() -> bool:
    """Check if we're using SQLite."""
    return "sqlite" in settings.database_url


# Portable UUID type - works with both PostgreSQL and SQLite
if is_sqlite():
    class GUID(TypeDecorator):
        """Platform-independent UUID type for SQLite."""
        impl = String(36)
        cache_ok = True

        def process_bind_param(self, value, dialect):
            if value is not None:
                if isinstance(value, uuid.UUID):
                    return str(value)
                return value
            return None

        def process_result_value(self, value, dialect):
            if value is not None:
                if not isinstance(value, uuid.UUID):
                    return uuid.UUID(value)
            return value
else:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    GUID = PG_UUID(as_uuid=True)


# Portable JSON type - works with both PostgreSQL and SQLite
class JSONType(TypeDecorator):
    """Platform-independent JSON type."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None


# Use JSONB for PostgreSQL, JSONType for SQLite
if is_sqlite():
    JSONB = JSONType
else:
    JSONB = postgresql.JSONB
