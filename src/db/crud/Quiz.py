import re
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
import json
from src.db.models import models, schema
from datetime import date

from datetime import datetime
from src.db.crud.QuizQuestion import QuizQuestionCrud
from src.db.crud.QuizOption import QuizOptionCrud

from sqlalchemy import select, update, delete, func




class QuizCrud:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    def praser(self, data):
        mcqs = []
        print(f"len of data {len(data)}")
        for i in data:
            try:
                parsed = json.loads(i)  # `i` is a JSON string response from OpenAI
                mcqs.extend(parsed)     # Assuming it's a list of MCQs
            except json.JSONDecodeError:
                print("Failed to parse response:", i)
        return mcqs

    async def create_quiz(db: AsyncSession, quiz_data):
        try:
            mcqs = quiz_data['mcqs']
            quiz_info = quiz_data['quizInfo']

            quiz = models.Quiz(
                course_id=quiz_info['course_id'],
                total_marks=len(mcqs),
                time=datetime.strptime(quiz_info["time"], "%H:%M").time(),
                date=datetime.strptime(quiz_info["date"], "%Y-%m-%d").date(),
                status="PENDING"
            )

            db.add(quiz)
            await db.commit()
            await db.refresh(quiz)
            await QuizQuestionCrud.create_quiz_question(db, mcqs, quiz.id)
            return quiz

        except Exception as e:
            print("❌ Error creating quiz:", e)
            raise


    async def get_single_quiz_by_id(db: AsyncSession, id):
        result = await db.execute(
            select(models.Quiz).where(
                models.Quiz.id == id,
            )
        )
        quiz = result.scalar_one_or_none()
        return quiz


    async def get_quiz_by_id(db: AsyncSession, id):
        try:
            result = await db.execute(
                select(models.Quiz).where(
                    models.Quiz.id == id,
                )
            )
            mcqs = []
            quiz = result.scalar_one_or_none()

            if quiz is None:
                raise ValueError("Quiz not found for the given ID")
            questions = await QuizQuestionCrud.get_questions_by_quiz_id(db, quiz.id)
            for i in questions:
                print(i.id)
            if questions is None:
                raise ValueError("Questions returned None")
            for question in questions:
                if question is None:
                    raise ValueError("Found None in questions list")
                question_options = await QuizOptionCrud.get_options_by_question_id(db, question.id)
                if question_options is None:
                    raise ValueError(f"Options returned None for question_id={question.id}")
                scanking = [correct.option_text for correct in question_options if correct.option_status == True]
                if not scanking:
                    continue
                correct_option = scanking[0]
                options = [option.option_text for option in question_options]
                options_ids = [option.id for option in question_options]
                mcqs.append({'statement':question.question_text, 'correct_answer':correct_option, 'options': options, 'options_ids': options_ids, 'question_id': question.id, 'quiz_id':id})
                print(mcqs)
            return mcqs, quiz
        except Exception as e:
            print(f"{e}{len(questions)}")

    async def get_course_id_by_quiz_id(db: AsyncSession, id: str):
        result = await db.execute(
            select(models.Quiz.course_id).where(
                models.Quiz.id == id,
            )
        )
        course_id = result.scalar_one_or_none()  # Gets the first row's value or None if not found
        return course_id

    async def update_quiz(db: AsyncSession, quiz_data):
        try:
            mcqs = quiz_data.get('mcqs')
            quiz_info = quiz_data.get('quizInfo')
            print(quiz_info)

            if mcqs is None:
                raise ValueError("Missing 'mcqs' in quiz_data")
            if not isinstance(mcqs, list):
                raise TypeError(f"'mcqs' should be a list, got {type(mcqs)}")

            print(f"Received {len(mcqs)} MCQs for update")

            quiz_id = await QuizQuestionCrud.update_quiz_question(db, mcqs)
            result = await db.execute(
                select(models.Quiz).where(
                    models.Quiz.id == quiz_id,
                )
            )
            quiz = result.scalar_one_or_none()

            if quiz is None:
                    # Quiz not found
                return None

                # Update the fields
            quiz.date = quiz_info['date']
            quiz.time = quiz_info['time']
            quiz.total_marks = len(mcqs)
            await db.commit()
            await db.refresh(quiz) 
            print(f"Quiz id {quiz_id} is updated")
            return quiz
        except Exception as e:
            print("❌ Error updating quiz crud:", e)
            raise


    async def get_quiz_by_status_pending_in_progress_and_day(db: AsyncSession):
        today = date.today()
        result = await db.execute(
            select(models.Quiz).where(
                models.Quiz.status.in_(['PENDING', 'IN_PROGRESS']),
                models.Quiz.date == today
            )
        )
        quizzes = result.scalars().all()
        return quizzes
    
 
    
    async def update_quiz_status_in_progress_by_id(db: AsyncSession, id):
        result = await db.execute(
            select(models.Quiz).where(
                models.Quiz.id == id,
            )
        )
        quiz = result.scalar_one_or_none()
        if quiz:
            quiz.status = "IN_PROGRESS"
            await db.commit() 
            await db.refresh(quiz)

    async def update_quiz_status_complete_by_id(db: AsyncSession, id):
        result = await db.execute(
            select(models.Quiz).where(
                models.Quiz.id == id,
            )
        )
        quiz = result.scalar_one_or_none()
        if quiz:
            quiz.status = "COMPLETE"
            await db.commit() 
            await db.refresh(quiz)


    async def get_quizes_course_id(db: AsyncSession, course_id):
        result = await db.execute(
            select(models.Quiz).where(
                models.Quiz.course_id == course_id,
                models.Quiz.status.in_(["COMPLETE", "PENDING"])
            )
        )
        quizzes = result.scalars().all()
        return quizzes
    
    async def get_quizes_course_id_status_pending(db: AsyncSession, course_id):
        result = await db.execute(
            select(models.Quiz).where(
                models.Quiz.course_id == course_id,
                models.Quiz.status.in_(["IN_PROGRESS"])
            )
        )
        quizzes = result.scalars().all()
        return quizzes