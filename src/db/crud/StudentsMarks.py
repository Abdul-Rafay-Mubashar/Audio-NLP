from src.db.models import models, schema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from fastapi_jwt_auth import AuthJWT
from src.db.models import get_db

from fastapi import APIRouter, Depends, HTTPException, status as http_status


class MarksCrud:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_marks(db: AsyncSession, course_id, user_id, totel_marks, obtained_marks, quiz_id):
        db_marks = models.StudentMark(
            course_id=course_id,
            quiz_id=quiz_id,
            total_marks=totel_marks,
            obtained_marks= obtained_marks,
            student_id = user_id
        )
        db.add(db_marks)
        await db.commit()
        await db.refresh(db_marks)

    
    async def get_marks_bystudent_id_quiz_id(db: AsyncSession, student_id, quiz_id):
        result = await db.execute(
            select(models.StudentMark).where(
                models.StudentMark.quiz_id == quiz_id,
                models.StudentMark.student_id == student_id
            )
        )
        marks = result.scalar_one_or_none()  # Gets the first row's value or None if not found
        return marks
    
    async def get_marks_with_usernames_by_quiz_id(db: AsyncSession, quiz_id: int):
        result = await db.execute(
            select(
                models.StudentMark.id,
                models.StudentMark.student_id,
                models.StudentMark.total_marks,
                models.StudentMark.obtained_marks,
                models.User.user_name
            ).join(models.User, models.StudentMark.student_id == models.User.id).where(models.StudentMark.quiz_id == quiz_id)
        )
        rows = result.all()

        # Convert rows to list of dicts
        marks_list = []
        for row in rows:
            marks_list.append({
                "id": row.id,
                "student_id": row.student_id,
                "total_marks": row.total_marks,
                "obtained_marks": row.obtained_marks,
                "user_name": row.user_name
            })
        return marks_list
    
    async def get_quiz_with_course_id_by_quiz_id_with_marks(db: AsyncSession, course_id: int):
        try:

            # Step 2: Get marks where mark.quiz_id IN (quiz ids of that course)
            result = await db.execute(
                select(models.StudentMark, models.Quiz)
                .join(models.Quiz, models.StudentMark.quiz_id == models.Quiz.id)
                .where(models.Quiz.course_id == course_id)
            )

            data = []
            for mark, quiz in result.all():
                data.append({
                    "quiz_id": quiz.id,
                    "quiz_date": quiz.date,
                    "quiz_time": quiz.time,
                    "total_marks": quiz.total_marks,
                    "student_id": mark.student_id,
                    "obtained_marks": mark.obtained_marks
                })

            return data

        except Exception as e:
            print(f"❌ Error fetching marks and quizzes: {e}")
            raise