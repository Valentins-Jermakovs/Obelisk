# =====================================================
#                       imports
# =====================================================
from jose import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv

# =====================================================
#                   .env initialization
# =====================================================
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# =====================================================
#                 HTTP bearer scheme
# =====================================================
bearer_scheme = HTTPBearer()

# =====================================================
#                   functions
# =====================================================

# Validate access token
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = credentials.credentials

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )

    return payload


# Administrator access
async def admin_required(
    payload: dict = Depends(validate_token)
):
    if "admin" not in payload.get("roles", []):
        raise HTTPException(
            status_code=403,
            detail="Forbidden"
        )

    return payload


# Librarian access
async def librarian_required(
    payload: dict = Depends(validate_token)
):
    if "librarian" not in payload.get("roles", []):
        raise HTTPException(
            status_code=403,
            detail="Forbidden"
        )

    return payload