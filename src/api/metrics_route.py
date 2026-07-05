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
# =========================================================================

# =========================================================================
#                                Router
# =========================================================================
# Router object
router = APIRouter(
    prefix="/metrics",
    tags=["Metrics services"],
)

# =========================================================================
#                               Endpoints
# =========================================================================
# =============== Endpoint for getting metrics =============================
@router.get("/stats", response_model=SystemMetrics)
async def metrics(
    payload: dict = Depends(admin_required)
):

    # Return current system metrics
    return SystemMetrics(
        cpu_percent=psutil.cpu_percent(),
        memory_percent=psutil.virtual_memory().percent,
        memory_used_mb=round(psutil.virtual_memory().used / 1024 / 1024),
    )