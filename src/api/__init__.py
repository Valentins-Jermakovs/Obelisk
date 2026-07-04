# =====================================================
#                   imports
# =====================================================
from fastapi import APIRouter
from .metrics_route import router as metrics_router
from .author_route import router as author_router
# =====================================================


# =====================================================
#               Router object and includes
# =====================================================
main_router = APIRouter()
main_router.include_router(metrics_router)
main_router.include_router(author_router)
# =====================================================