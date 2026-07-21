# =====================================================
#                        Imports
# =====================================================

# Libraries:
import psutil
from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime

# Dependencies:
from config.db_dependency import get_db

# Schemas:
from schemas.metrics import (
    SystemMetrics, 
    AuditLogsResponse
)

# Utils:
from utils.token_utils import admin_required

# Services:
from services.audit_service import (
    export_audit_logs, 
    get_audit_logs
)

# Models:
from models import (
    AuditAction, 
    EntityType
)



# Router object for export
router = APIRouter(
    prefix="/metrics",
    tags=["Metrics services and audit logs"],
)



# =====================================================
#                       Endpoints
# =====================================================

# Return server metric data
# Administrator required
@router.get(
    "/stats", 
    response_model=SystemMetrics,
    summary="Return server metric data, Admin required"
)
async def metrics(
    payload: dict = Depends(admin_required)
) -> SystemMetrics:
    
    # Return current system metrics
    return SystemMetrics(
        cpu_percent=psutil.cpu_percent(),
        memory_percent=psutil.virtual_memory().percent,
        memory_used_mb=round(psutil.virtual_memory().used / 1024 / 1024),
    )



# Get audit logs with filters and pagination
# Administrator required
@router.get(
    "/audit",
    response_model=AuditLogsResponse,
    summary="Get audit logs with filters and pagination. Admin required"
)
async def get_audit_logs_route(
    query: str | None = Query(
        default=None,
        description="Search in description and metadata"
    ),

    user_id: int | None = Query(
        default=None,
        description="Filter by user ID"
    ),

    action: AuditAction | None = Query(
        default=None,
        description="Filter by action"
    ),

    entity_type: EntityType | None = Query(
        default=None,
        description="Filter by entity type"
    ),

    success: bool | None = Query(
        default=None,
        description="Filter by operation status"
    ),

    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of records per page"
    ),

    offset: int = Query(
        default=0,
        ge=0,
        description="Pagination offset"
    ),
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
) -> AuditLogsResponse:

    # Get audit logs
    logs = await get_audit_logs(
        session=session,
        query=query,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        success=success,
        limit=limit,
        offset=offset,
    )

    return logs


# Get audit logs in CSV format
# Administrator role required
@router.get("/export")
async def export_audit_route(
    user_id: int | None = Query(
        default=None,
        description="Filter by user ID"
    ),

    action: AuditAction | None = Query(
        default=None,
        description="Filter by action"
    ),

    entity_type: EntityType | None = Query(
        default=None,
        description="Filter by entity type"
    ),

    success: bool | None = Query(
        default=None,
        description="Filter by operation status"
    ),

    start_date: datetime | None = Query(
        default=None,
        description="Start date"
    ),

    end_date: datetime | None = Query(
        default=None,
        description="End date"
    ),

    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):

    # Generate CSV file
    file_path = await export_audit_logs(
        session=session,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        success=success,
        start_date=start_date,
        end_date=end_date,
    )


    # Return file
    return FileResponse(
        path=file_path,
        filename=file_path.split("/")[-1],
        media_type="text/csv"
    )