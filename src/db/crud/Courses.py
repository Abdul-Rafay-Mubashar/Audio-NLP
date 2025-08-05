from src.db.models import models, schema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from fastapi_jwt_auth import AuthJWT
from src.db.models import get_db
import setting
from fastapi import APIRouter, Depends, HTTPException, status as http_status


class CourseCrud:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session


    async def get_course_by_course_id(db: AsyncSession, course_id: str):
        result = await db.execute(
            select(models.Course).where(
                models.Course.id == course_id
            )
        )
        course = result.scalar_one_or_none()
        return course
