# =====================================================
#                        Imports
# =====================================================

# Libraries:
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any



# =====================================================
#                       Schemas
# =====================================================

# ===================Request schemas===================

# System metrics response schema
class SystemMetrics(BaseModel):

    cpu_percent: float = Field(
        ge=0, 
        le=100
    )

    memory_percent: float = Field(
        ge=0, 
        le=100
    )

    memory_used_mb: int = Field(ge=0)



# ===================Response schemas================

# Audit log response schema
class AuditLogResponse(BaseModel):

    id: int
    user_id: int | None
    action: str | None
    entity_type: str | None
    description: str
    success: bool
    meta: dict[str, Any]
    created_at: datetime



# Audit logs response schema
class AuditLogsResponse(BaseModel):

    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int
    has_more: bool