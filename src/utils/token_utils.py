# =====================================================
#                       imports
# =====================================================
from jose import jwt, JWTError, ExpiredSignatureError
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

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


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


# Administrator or Librarian
async def admin_or_librarian_required(
    payload: dict = Depends(validate_token)
):
    if "admin" not in payload.get("roles", []) and "librarian" not in payload.get("roles", []):
        raise HTTPException(
            status_code=403,
            detail="Forbidden"
        )
    return payload