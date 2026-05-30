import asyncio
import calendar
import json
from datetime import date as date_type, timedelta
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy import case, or_
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from db import get_session
from middleware.auth import verify_user_access
from models import Task
from schemas import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(tags=["tasks"])

# Priority sort ordering
_PRIORITY_ORDER = case(
    (Task.priority == "high", 1),
    (Task.priority == "medium", 2),
    (Task.priority == "low", 3),
    else_=4,
)


@router.get("/{user_id}/tasks", response_model=list[TaskRead], dependencies=[Depends(verify_user_access)])
async def list_tasks(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    search: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    completed: Optional[bool] = None,
) -> list[TaskRead]:
    """List all tasks for a user with optional filters."""
    query = select(Task).where(Task.user_id == user_id)

    if completed is not None:
        query = query.where(Task.completed == completed)
    if priority:
        query = query.where(Task.priority == priority)
    if category:
        query = query.where(Task.category == category)
    if search:
        query = query.where(
            or_(
                Task.title.ilike(f"%{search}%"),
                Task.category.ilike(f"%{search}%"),
            )
        )

    query = query.order_by(_PRIORITY_ORDER, Task.created_at.desc())
    result = await session.execute(query)
    return result.scalars().all()


@router.post("/{user_id}/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_user_access)])
async def create_task(
    user_id: str,
    body: TaskCreate,
    session: AsyncSession = Depends(get_session),
) -> TaskRead:
    """Create a new task for a user."""
    task = Task(
        user_id=user_id,
        title=body.title,
        priority=body.priority,
        category=body.category,
        due_date=body.due_date,
        due_time=body.due_time,
        recurring=body.recurring,
        reminder=body.reminder,
    )
    session.add(task)
    await session.flush()
    await session.refresh(task)
    return task


@router.patch("/{user_id}/tasks/{task_id}", response_model=TaskRead, dependencies=[Depends(verify_user_access)])
async def update_task(
    user_id: str,
    task_id: str,
    body: TaskUpdate,
    session: AsyncSession = Depends(get_session),
) -> TaskRead:
    """Update a task."""
    result = await session.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    session.add(task)
    await session.flush()
    await session.refresh(task)
    return task


@router.delete("/{user_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_user_access)])
async def delete_task(
    user_id: str,
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete a task."""
    result = await session.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await session.delete(task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{user_id}/tasks/{task_id}/complete", response_model=TaskRead, dependencies=[Depends(verify_user_access)])
async def complete_task(
    user_id: str,
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> TaskRead:
    """Mark a task as completed."""
    result = await session.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.completed = True
    session.add(task)
    await session.flush()
    await session.refresh(task)
    return task
