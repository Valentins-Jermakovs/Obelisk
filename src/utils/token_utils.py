# =====================================================
#                       imports
# =====================================================
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException
import os
from dotenv import load_dotenv

# =====================================================
#                   .env initialization
# =====================================================
load_dotenv()

# Save .env variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


# =====================================================
#                   functions
# =====================================================
def decode_access_token(token: str) -> dict:

    # Function returns None if token is invalid or expired
    # But if valid, return dict:
    #   {
    #       "sub": "1",
    #       "roles": ["user"],
    #       "exp": 1782892714,
    #       "iat": 1782892714
    #   }

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
            detail="Token expired"
        )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )