# ==================================================
#                       imports
# ==================================================
# Libraries:
from sqlmodel.ext.asyncio.session import AsyncSession
import csv
import os
from sqlmodel import select, or_, func, Text, cast
from datetime import date, datetime
from enum import Enum
# Models:
from models import AuditLog, AuditAction, EntityType



# ==================================================
#      Service functions - helpers and CRUD
# ==================================================


# Get audit logs with search and pagination
async def get_audit_logs(
    session: AsyncSession,
    query: str | None = None,
    user_id: int | None = None,
    action: AuditAction | None = None,
    entity_type: EntityType | None = None,
    success: bool | None = None,
    limit: int = 20,
    offset: int = 0,
):

    # Base query
    statement = select(AuditLog)


    # Search by description and metadata
    if query:

        # Normalize search query
        q = query.strip().lower()

        if q:

            statement = statement.where(
                or_(
                    # Search in description field
                    AuditLog.description.ilike(
                        f"%{q}%"
                    ),

                    # Search inside JSON metadata
                    cast(
                        AuditLog.meta,
                        Text
                    ).ilike(
                        f"%{q}%"
                    )
                )
            )


    # Filter by user ID
    if user_id is not None:

        statement = statement.where(
            AuditLog.user_id == user_id
        )


    # Filter by action
    if action is not None:

        statement = statement.where(
            AuditLog.action == action
        )


    # Filter by entity type
    if entity_type is not None:

        statement = statement.where(
            AuditLog.entity_type == entity_type
        )


    # Filter by operation status
    if success is not None:

        statement = statement.where(
            AuditLog.success == success
        )


    # Count total records before pagination
    count_statement = (
        select(func.count())
        .select_from(
            statement.subquery()
        )
    )


    total = (
        await session.exec(
            count_statement
        )
    ).one()



    # Sort newest logs first
    statement = (
        statement
        .order_by(
            AuditLog.created_at.desc()
        )
        .offset(offset)
        .limit(limit)
    )


    # Execute query
    result = await session.exec(
        statement
    )

    logs = result.all()



    # Prepare response items
    items = []


    for log in logs:

        items.append(
            {
                "id": log.id,

                "user_id": log.user_id,

                "action": (
                    log.action.value
                    if log.action
                    else None
                ),

                "entity_type": (
                    log.entity_type.value
                    if log.entity_type
                    else None
                ),

                "description": log.description,

                "success": log.success,

                "meta": log.meta,

                "created_at": log.created_at,
            }
        )



    # Return paginated response
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(items) < total,
    }


# Resolve user id - helper function
def _resolve_user_id(payload: dict | None) -> int:

    # If no payload, return 0
    if not payload:
        return 0

    # If no sub or user id in payload, return 0
    raw_user_id = payload.get("sub") or payload.get("user_id")
    if raw_user_id is None:
        return 0

    # Try to convert raw user id into an integer
    try:
        return int(raw_user_id)
    except (TypeError, ValueError):
        return 0


# Write audit log
async def write_audit_log(
    session: AsyncSession,
    payload: dict | None,
    action: AuditAction,
    description: str,
    entity_type: EntityType | None = None,
    success: bool = True,
    **meta,
):
    
    # Write audit log
    session.add(
        AuditLog(
            user_id=_resolve_user_id(payload),
            action=action,
            entity_type=entity_type,
            description=description,
            success=success,
            meta=serialize_audit_data(meta)
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
    
    # Write failed audit log
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


# Serialize audit data - used for audit log meta data
# Helper function for serializing data in JSON
def serialize_audit_data(value):

    # If the value is a dictionary, serialize it:
    if isinstance(value, dict):
        return {
            k: serialize_audit_data(v)
            for k, v in value.items()
        }

    # If the value is a list or tuple, serialize it:
    if isinstance(value, (list, tuple, set)):
        return [
            serialize_audit_data(v)
            for v in value
        ]

    # If the value is a date or datetime, serialize it:
    if isinstance(value, (date, datetime)):
        return value.isoformat()

    # If the value is an Enum, serialize it:
    if isinstance(value, Enum):
        return value.value

    # Return serialized data
    return value

# Export audit logs to CSV
async def export_audit_logs(
    session: AsyncSession,
    user_id: int | None = None,
    action: AuditAction | None = None,
    entity_type: EntityType | None = None,
    success: bool | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> str:

    # Base query
    statement = select(AuditLog)


    # Filters:

    # Filter by user
    if user_id is not None:
        statement = statement.where(
            AuditLog.user_id == user_id
        )


    # Filter by action
    if action is not None:
        statement = statement.where(
            AuditLog.action == action
        )


    # Filter by entity type
    if entity_type is not None:
        statement = statement.where(
            AuditLog.entity_type == entity_type
        )


    # Filter by success status
    if success is not None:
        statement = statement.where(
            AuditLog.success == success
        )


    # Filter by date range
    if start_date:
        statement = statement.where(
            AuditLog.created_at >= start_date
        )
    if end_date:
        statement = statement.where(
            AuditLog.created_at <= end_date
        )


    # Sort newest first
    statement = statement.order_by(
        AuditLog.created_at.desc()
    )


    # Execute query
    result = await session.exec(statement)
    # Get results
    logs = result.all()



    # Create export directory
    export_dir = "exports"

    os.makedirs(
        export_dir,
        exist_ok=True
    )

    # Generate filename
    filename = (
        f"audit_logs_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

    # Create file path
    file_path = os.path.join(
        export_dir,
        filename
    )

    # Write CSV
    with open(
        file_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)


        # Header
        writer.writerow([
            "id",
            "user_id",
            "action",
            "entity_type",
            "description",
            "success",
            "meta",
            "created_at",
        ])


        # Data
        for log in logs:

            writer.writerow([
                log.id,
                log.user_id,
                log.action.value,
                log.entity_type.value
                if log.entity_type
                else None,
                log.description,
                log.success,
                log.meta,
                log.created_at,
            ])


    return file_path