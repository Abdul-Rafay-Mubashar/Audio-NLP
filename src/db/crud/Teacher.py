from src.db.models import models, schema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from fastapi_jwt_auth import AuthJWT
from src.db.models import get_db

from fastapi import APIRouter, Depends, HTTPException, status as http_status


class TeacherCrud:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_teacher(db: AsyncSession, user: schema.User):
        db_teacher = models.User(
            email=user.email,
            password=user.password,
            user_name=user.first_name + " " + user.last_name,
            is_admin=user.is_admin,
        )
        db.add(db_teacher)
        await db.commit()
        await db.refresh(db_teacher)
        return db_teacher

    async def get_teacher_by_email(db: AsyncSession, email: str):
        result = await db.execute(
            select(models.User).where(
                models.User.email == email, models.User.is_admin == True
            )
        )
        teacher = result.scalar_one_or_none()
        return teacher

    async def get_teacher_by_id(db: AsyncSession, id: str):
        result = await db.execute(
            select(models.User).where(
                models.User.id == id, models.User.is_admin == True
            )
        )
        teacher = result.scalar_one_or_none()
        return teacher

    async def get_current_teacher_from_token(
        Authorize: AuthJWT = Depends(), db: AsyncSession = Depends(get_db)
    ):
        try:
            Authorize.jwt_required()
            teacher_email = Authorize.get_jwt_subject()
            result = await db.execute(
                select(models.User).where(models.User.email == teacher_email)
            )
            teacher = result.scalar_one_or_none()
        except Exception as e:
            raise HTTPException(
                status_code=401, detail="Invalid token or not authenticated"
            )

        if teacher is None:
            raise HTTPException(status_code=404, detail="User not found")

        return teacher


    async def get_teacher_by_id(db: AsyncSession, id: str):
        result = await db.execute(
            select(models.User).where(
                models.User.id == id, models.User.is_admin == True
            )
        )
        user = result.scalar_one_or_none()
        return user