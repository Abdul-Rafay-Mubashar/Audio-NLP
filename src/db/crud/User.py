from src.db.models import models, schema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from fastapi_jwt_auth import AuthJWT
from src.db.models import get_db

from fastapi import APIRouter, Depends, HTTPException, status as http_status


class UserCrud:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(db: AsyncSession, user: schema.User):
        db_user = models.User(
            email=user.email,
            password=user.password,
            user_name=user.first_name + " " + user.last_name,
            is_admin=user.is_admin,
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def get_user_by_email(db: AsyncSession, email: str):
        result = await db.execute(
            select(models.User).where(
                models.User.email == email, models.User.is_admin == False
            )
        )
        user = result.scalar_one_or_none()
        return user

    async def get_user_by_id(db: AsyncSession, id: str):
        result = await db.execute(
            select(models.User).where(
                models.User.id == id, models.User.is_admin == False
            )
        )
        user = result.scalar_one_or_none()
        return user

    async def get_current_user_from_token(
        Authorize: AuthJWT = Depends(), db: AsyncSession = Depends(get_db)
    ):
        try:
            Authorize.jwt_required()
            user_email = Authorize.get_jwt_subject()
            result = await db.execute(
                select(models.User).where(models.User.email == user_email)
            )
            user = result.scalar_one_or_none()
        except Exception as e:
            raise HTTPException(
                status_code=401, detail="Invalid token or not authenticated"
            )

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        return user


    async def get_user_emails_from_course_id(db: AsyncSession, ids: list):
        result = await db.execute(
            select(models.User.email).where(
                models.User.id.in_(ids), models.User.is_admin == False
            )
        )
        users = result.scalars().all()
        return users


