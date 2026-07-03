# =====================================================
#                       imports
# =====================================================
from .database import AsyncSessionLocal
# =====================================================

# =====================================================
#           Dependency injection
# =====================================================
async def get_db():
    async with AsyncSessionLocal() as session:           # Create session
        yield session                                    # Return session to caller
# =====================================================