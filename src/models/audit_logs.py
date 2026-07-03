# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Any
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
# =====================================================


# Audit log model
class AuditLog(SQLModel, table=True):

    # Tablename
    __tablename__ = "audit_logs"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Who did it?
    user_id: int = Field(index=True)

    # Action type
    action: str = Field(index=True)

    # Entity type
    entity_type: str = Field(index=True)  # "book", "reader", "loan"

    # Operation status
    success: bool = Field(default=True)

    # Meta data (JSON)
    meta: dict[str, Any] = Field(
        sa_column=Column(JSONB),
        default_factory=dict
    )

    # When it happened
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        index=True
    )