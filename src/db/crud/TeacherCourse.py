from src.db.models import models, schema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from fastapi_jwt_auth import AuthJWT
from src.db.models import get_db
import setting
from fastapi import APIRouter, Depends, HTTPException, status as http_status


class TeacherCourseCrud:
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

    async def get_course_by_user_id(db: AsyncSession, user_id: str):
        result = await db.execute(
            select(models.TeacherCourse).where(
                models.TeacherCourse.student_id == user_id
            )
        )
        user_courses = result.scalars().all()
        return user_courses
    
    async def get_section_by_user_id_course_name(db: AsyncSession, user_id: str, name):
        course_id_prefix = f"{setting.CURRENT_SEMESTER}-{name}%"
        result = await db.execute(
            
            select(models.TeacherCourse).where(
                models.TeacherCourse.student_id == user_id,
                models.TeacherCourse.course_id.like(course_id_prefix)
            )
        )
        user_courses = result.scalars().all()
        return user_courses

    async def get_users_from_course_id(db: AsyncSession, id: str):
        result = await db.execute(    
            select(models.TeacherCourse.student_id).where(
                models.TeacherCourse.course_id == id

            )
        )
        course_user = result.scalars().all()
        return course_user