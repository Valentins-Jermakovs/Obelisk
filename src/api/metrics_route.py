# =========================================================================
#                               imports
# =========================================================================
# Libraries:
import psutil
from fastapi import APIRouter, Depends
# Schemas:
from schemas.metrics import SystemMetrics
# Utils:
from utils.token_utils import admin_required


# Router object for export
router = APIRouter(
    prefix="/metrics",
    tags=["Metrics services"],
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