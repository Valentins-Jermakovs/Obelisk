# =====================================================
#                   imports
# =====================================================
from fastapi import APIRouter
from .metrics import router as metrics_router
# =====================================================


# =====================================================
#               Router object and includes
# =====================================================
main_router = APIRouter()
main_router.include_router(metrics_router)
# =====================================================