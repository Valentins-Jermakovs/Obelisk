# ==================================================
#                       imports
# ==================================================
# Libraries:
from sqlmodel.ext.asyncio.session import AsyncSession
# Models:
from models import AuditLog, AuditAction, EntityType



# ==================================================
#      Service functions - helpers and CRUD
# ==================================================
# Write audit log
async def write_audit_log(
    session: AsyncSession,
    payload: dict,
    action: AuditAction,
    description: str,
    entity_type: EntityType | None = None,
    success: bool = True,
    **meta,
):
    session.add(
        AuditLog(
            user_id=int(payload["sub"]),
            action=action,
            entity_type=entity_type,
            description=description,
            success=success,
            meta=meta,
        )
    )


# Write failed audit log
async def write_failed_audit_log(
    session: AsyncSession,
    payload: dict,
    action: AuditAction,
    description: str,
    entity_type: EntityType | None = None,
    error: str | None = None,
    **meta,
):
    await write_audit_log(
        session=session,
        payload=payload,
        action=action,
        entity_type=entity_type,
        description=description,
        success=False,
        error=error,
        **meta,
    )

# Usage example:
#
# await write_audit_log(
#     session=session,
#     payload=payload,
#     action=AuditAction.CREATE,
#     entity_type=EntityType.BOOK,
#     description=f"Created book '{book.title}'",
#     isbn=book.isbn,
# )


# What stored in database:
# {
#   "user_id": 1,
#   "action": "create",
#   "entity_type": "book",
#   "description": "Created book '1984'",
#   "meta": {
#       "isbn": "9780451524935"
#   }
# }