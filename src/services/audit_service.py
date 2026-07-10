# ==================================================
#                       imports
# ==================================================
# Libraries:
from sqlmodel.ext.asyncio.session import AsyncSession
import csv
import os
from datetime import datetime
from sqlmodel import select
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


    # Filters

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