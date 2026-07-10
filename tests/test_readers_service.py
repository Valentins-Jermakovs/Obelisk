import asyncio
import os
import sys
from pathlib import Path
from sqlmodel import SQLModel, create_engine

# Ensure project src is importable
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

import models  # noqa: F401
from models import DimReader
from services.reader_service import search_readers

DB_PATH = "/tmp/obelisk_test_readers.db"
SYNC_URL = f"sqlite:///{DB_PATH}"
ASYNC_URL = f"sqlite+aiosqlite:///{DB_PATH}"


async def setup_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    sync_engine = create_engine(SYNC_URL)
    SQLModel.metadata.create_all(sync_engine)

    async_engine = create_async_engine(ASYNC_URL, echo=False)
    AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    return AsyncSessionLocal


def test_search_by_phone():
    async def _run():
        AsyncSessionLocal = await setup_db()
        async with AsyncSessionLocal() as session:
            # create a reader with a phone number
            reader = DimReader(full_name="Test Reader", email="t@example.com", phone="+71234567890")
            session.add(reader)
            await session.commit()
            await session.refresh(reader)

            # search by part of the phone number
            res = await search_readers(session=session, query="23456", limit=10, offset=0)
            assert isinstance(res, dict)
            assert res["total"] == 1
            assert res["items"][0]["phone"] == "+71234567890"

    asyncio.run(_run())


if __name__ == '__main__':
    asyncio.run(test_search_by_phone())
