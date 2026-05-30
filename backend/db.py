import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

_log = logging.getLogger(__name__)

from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import text

load_dotenv()

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        database_url = os.getenv("DATABASE_URL", "")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set.")
        _engine = _build_engine(database_url)
    return _engine


def set_engine(engine: AsyncEngine) -> None:
    global _engine
    _engine = engine


def _build_engine(database_url: str) -> AsyncEngine:
    is_sqlite = database_url.startswith("sqlite")

    if is_sqlite:
        connect_args: dict = {"check_same_thread": False}
        kwargs: dict = {"echo": False, "connect_args": connect_args}
    else:
        from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
        parsed = urlparse(database_url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        params.pop("sslmode", None)
        params.pop("channel_binding", None)
        clean_url = urlunparse(parsed._replace(query=urlencode(params, doseq=True)))

        connect_args = {"ssl": "require"}
        kwargs = {
            "echo": False,
            "connect_args": connect_args,
            "pool_pre_ping": True,
            "pool_size": 5,
            "max_overflow": 10,
            "pool_recycle": 300,
        }
        database_url = clean_url

    return create_async_engine(database_url, **kwargs)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    engine = get_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    from models import Task, Conversation, Message  # noqa: F401

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Task.__table__.create, checkfirst=True)
        await conn.run_sync(Conversation.__table__.create, checkfirst=True)
        await conn.run_sync(Message.__table__.create, checkfirst=True)

    # Add new columns if needed (PostgreSQL only)
    if "sqlite" not in str(engine.url):
        await _migrate_task_columns(engine)

    yield

    await engine.dispose()
    set_engine(None)


async def _migrate_task_columns(engine: AsyncEngine) -> None:
    statements = [
        "ALTER TABLE task ADD COLUMN IF NOT EXISTS priority VARCHAR(6)",
        "ALTER TABLE task ADD COLUMN IF NOT EXISTS category VARCHAR(50)",
        "ALTER TABLE task ADD COLUMN IF NOT EXISTS tags TEXT",
        "ALTER TABLE task ADD COLUMN IF NOT EXISTS due_date DATE",
        "ALTER TABLE task ADD COLUMN IF NOT EXISTS due_time VARCHAR(5)",
        "ALTER TABLE task ADD COLUMN IF NOT EXISTS recurring VARCHAR(7)",
        "ALTER TABLE task ADD COLUMN IF NOT EXISTS reminder BOOLEAN DEFAULT false",
    ]
    async with engine.begin() as conn:
        for sql in statements:
            try:
                await conn.execute(text(sql))
            except Exception:
                pass
