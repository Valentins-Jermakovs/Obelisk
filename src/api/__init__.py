# =====================================================
#                   imports
# =====================================================
# Libraries:
from fastapi import APIRouter
# Routers
from .metrics_route import router as metrics_router
from .author_route import router as author_router
from .library_route import router as library_router
from .librarian_route import router as librarian_router
from .reader_route import router as reader_router
from .genre_route import router as genre_router
from .language_route import router as language_router
from .shelf_route import router as shelf_router
from .book_route import router as book_router
from .loan_route import router as loan_router
from .book_copy_route import router as book_copy_router

# This will be the main router object
main_router = APIRouter()


# =====================================================
#         Connect app routes to the main router
# =====================================================

main_router.include_router(metrics_router)
main_router.include_router(author_router)
main_router.include_router(library_router)
main_router.include_router(librarian_router)
main_router.include_router(reader_router)
main_router.include_router(genre_router)
main_router.include_router(language_router)
main_router.include_router(shelf_router)
main_router.include_router(book_router)
main_router.include_router(loan_router)
main_router.include_router(book_copy_router)
