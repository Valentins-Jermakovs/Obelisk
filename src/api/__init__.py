# =====================================================
#                   imports
# =====================================================
from fastapi import APIRouter
from .metrics_route import router as metrics_router
from .author_route import router as author_router
from .library_route import router as library_router
from .librarian_route import router as librarian_router
from .reader_route import router as reader_router
from .genre_route import router as genre_router
from .language_route import router as language_router
# =====================================================


# =====================================================
#               Router object and includes
# =====================================================
main_router = APIRouter()
main_router.include_router(metrics_router)
main_router.include_router(author_router)
main_router.include_router(library_router)
main_router.include_router(librarian_router)
main_router.include_router(reader_router)
main_router.include_router(genre_router)
main_router.include_router(language_router)
# =====================================================