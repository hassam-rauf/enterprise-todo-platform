# Stub - Dapr jobs disabled for Vercel deployment
from sqlmodel.ext.asyncio.session import AsyncSession

async def register_reminder_job() -> None:
    pass

async def scan_and_publish_reminders(session: AsyncSession) -> None:
    pass
