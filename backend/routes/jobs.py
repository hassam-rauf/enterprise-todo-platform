# Stub - Dapr jobs disabled for Vercel deployment
from fastapi import APIRouter, Depends, Response, status
from sqlmodel.ext.asyncio.session import AsyncSession
from db import get_session

router = APIRouter(tags=["jobs"])

@router.post("/job/reminder-scan", status_code=status.HTTP_204_NO_CONTENT)
async def handle_reminder_scan(
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Stub - Dapr Jobs callback disabled on Vercel."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)
