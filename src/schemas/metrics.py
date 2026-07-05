# ===================================================
#                       imports
# ===================================================
from pydantic import BaseModel, Field
# ==================================================


# System metrics response schema
class SystemMetrics(BaseModel):
    cpu_percent: float = Field(..., ge=0, le=100)
    memory_percent: float = Field(..., ge=0, le=100)
    memory_used_mb: int = Field(..., ge=0)