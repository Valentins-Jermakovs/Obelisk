# =========================================================================
#                               imports
# =========================================================================
# Libraries:
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
# Utils:
import utils.token_utils as token_utils
# =========================================================================

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Dependencies
async def get_current_user(
    token: str = Depends(oauth2_scheme)
):
    payload = token_utils.decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    return payload