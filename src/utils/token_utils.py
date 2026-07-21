# =====================================================
#                        Imports
# =====================================================

# Libraries:
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


#   HTTP bearer scheme
bearer_scheme = HTTPBearer()



# =====================================================
#                  Utils functions
# =====================================================

# Validate access token
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    # Get the token from the authorization header
    token = credentials.credentials

    try:
        # Decode the token
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    # Check the token's expiration date - Error
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )

    # Check the token's signature - Error
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )



# Administrator access
async def admin_required(
    payload: dict = Depends(validate_token)
):
    # Check the token's role
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
    # Check the token's role
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
    # Check the token's role
    if "admin" not in payload.get("roles", []) and "librarian" not in payload.get("roles", []):
        raise HTTPException(
            status_code=403,
            detail="Forbidden"
        )
    return payload