import re
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
import json
from src.db.models import models, schema
from datetime import datetime
from sqlalchemy import select, update, delete, func



class QuizOptionCrud:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session



    async def create_quiz_option(db: AsyncSession, options, question_id, correct_option):
        try:
            for option in options:
                status = False
                if option == correct_option:
                    status = True
                option = models.QuestionsOptions(
                    question_id=question_id,
                    option_text=option,
                    option_status=status
                )

                db.add(option)
                await db.flush() 

                await db.commit()
                await db.refresh(option)


        except Exception as e:
            print(f"in option crud{e}")

            raise

    async def get_options_by_question_id(db: AsyncSession, id):
        print(f"Id in Option Crud: {id}")
        result = await db.execute(
            select(models.QuestionsOptions).where(
                models.QuestionsOptions.question_id == id,
            )
        )

        questions = result.scalars().all()
        return questions
    
    async def get_option_by__id(db: AsyncSession, id):
        result = await db.execute(
            select(models.QuestionsOptions).where(
                models.QuestionsOptions.id == id,
            )
        )
        
        questions = result.scalar_one_or_none()
        return questions