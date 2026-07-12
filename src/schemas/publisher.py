# ===================================================
#                       imports
# ===================================================
# Libraries:
from pydantic import BaseModel, Field




# ===================================================
#                       schemas
# ===================================================

# Publisher create schema
class PublisherCreate(BaseModel):

    # Publisher name
    name: str = Field(
        min_length=1,
        max_length=255
    )

    # Publisher country
    country: str | None = None

# Publisher update schema
class PublisherUpdate(BaseModel):

    # Publisher name
    name: str | None = Field(
        default=None, 
        min_length=1, 
        max_length=255
    )

    # Publisher country
    country: str | None = None


# Read schema
class PublisherRead(BaseModel):

    # Publisher ID
    id: int

    # Publisher name
    name: str

    # Publisher country
    country: str | None = None


    class Config:
        from_attributes = True


# Search filter schema
class PublisherSearch(BaseModel):

    # Search query
    query: str | None = None

    # Filter by country
    country: str | None = None

    # Pagination limit
    limit: int = Field(
        default=10,
        ge=1,
        le=100
    )

    # Pagination offset
    offset: int = Field(
        default=0,
        ge=0
    )


# Paginated response schema
class PublisherListResponse(BaseModel):

    # Publisher list
    items: list[PublisherRead]

    # Total records count
    total: int

    # Current limit
    limit: int

    # Current offset
    offset: int

    # Returned records count
    returned: int


# Delete response schema
class PublisherDeleteResponse(BaseModel):

    # Delete status
    status: str

    # Deleted publisher ID
    publisher_id: int