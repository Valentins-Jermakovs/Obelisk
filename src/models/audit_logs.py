# =====================================================
#                       imports
# =====================================================
from datetime import datetime
from enum import Enum
from typing import Any
from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


# =====================================================
#                       enums
# =====================================================

# Entity types
class EntityType(str, Enum):
    BOOK = "book"
    BOOK_COPY = "book_copy"
    READER = "reader"
    AUTHOR = "author"
    GENRE = "genre"
    LANGUAGE = "language"
    LIBRARY = "library"
    LIBRARIAN = "librarian"
    SHELF = "shelf"
    LOAN = "loan"


# Audit actions
class AuditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

    ISSUE = "issue"
    RETURN = "return"

    OTHER = "other"


# =====================================================
#                       models
# =====================================================

class AuditLog(SQLModel, table=True):

    __tablename__ = "audit_logs"


    # Primary key
    id: int | None = Field(
        default=None,
        primary_key=True
    )


    # Who performed action
    user_id: int = Field(
        index=True
    )


    # Action type
    action: AuditAction = Field(
        index=True
    )


    # Object type
    entity_type: EntityType | None = Field(
        default=None,
        index=True
    )


    # Human-readable description
    description: str = Field(
        index=True
    )


    # Was operation successful?
    success: bool = Field(
        default=True
    )


    # Additional information
    meta: dict[str, Any] = Field(
        sa_column=Column(JSON),
        default_factory=dict
    )


    # Time
    created_at: datetime = Field(
        default_factory=datetime.now,
        index=True
    )