from src.db.models import models, schema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from fastapi_jwt_auth import AuthJWT
from src.db.models import get_db

from fastapi import APIRouter, Depends, HTTPException, status as http_status


class AnswerCrud:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_awnser(db: AsyncSession, answer, course_id, user_id):
        db_answer = models.StudentAnswer(
            course_id=course_id,
            question_id=answer['question_id'],
            quiz_id=answer['quiz_id'],
            answer_text=answer['your_answer'],
            correct_answer= answer['correct_answer'],
            student_id = user_id
        )
        db.add(db_answer)
        await db.commit()
        await db.refresh(db_answer)
        if db_answer.answer_text == db_answer.correct_answer:
            return True
        return None

 