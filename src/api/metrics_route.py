# ===================================================
#                       imports
# ===================================================
# Libraries:
import psutil
from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime
# Dependencies:
from config.db_dependency import get_db
# Schemas:
from schemas.metrics import SystemMetrics
# Utils:
from utils.token_utils import admin_required
# Services:
from services.audit_service import export_audit_logs
# Models:
from models import AuditAction, EntityType


# Router object for export
router = APIRouter(
    prefix="/metrics",
    tags=["Metrics services and audit logs"],
)

# ==================================================
#       routes - metric and audit data
# ==================================================

# Return server metric data
# Administrator required
@router.get(
    "/stats", 
    response_model=SystemMetrics,
    summary="Return server metric data, Admin required"
)
async def metrics(
    payload: dict = Depends(admin_required)
):
    # Return current system metrics
    return SystemMetrics(
        cpu_percent=psutil.cpu_percent(),
        memory_percent=psutil.virtual_memory().percent,
        memory_used_mb=round(psutil.virtual_memory().used / 1024 / 1024),
    )


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