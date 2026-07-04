# =========================================================================
#                               imports
# =========================================================================
# Libraries:
import psutil
from fastapi import APIRouter, Depends, HTTPException
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
@router.get("/stats")
async def metrics(
    payload: dict = Depends(admin_required)
):

    # Return current system metrics
    return {
        # CPU usage percentage
        "cpu_percent": psutil.cpu_percent(),

        # Memory usage percentage
        "memory_percent": psutil.virtual_memory().percent,

        # Used memory in megabytes
        "memory_used_mb":
            round(psutil.virtual_memory().used / 1024 / 1024),
    }