# =====================================================
#                   imports
# =====================================================
from fastapi import APIRouter
from .hello_world import router as hello_world_router
# =====================================================


# =====================================================
#               Router object and includes
# =====================================================
main_router = APIRouter()
main_router.include_router(hello_world_router)
# =====================================================