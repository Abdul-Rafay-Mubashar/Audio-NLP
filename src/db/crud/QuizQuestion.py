import re
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
import json
from src.db.models import models, schema
from datetime import datetime
from src.db.crud.QuizOption import QuizOptionCrud
from sqlalchemy import select, update, delete, func



class QuizQuestionCrud:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session



    async def create_quiz_question(db: AsyncSession, mcqs, quiz_id):
        try:
            print(mcqs, )
            for mcq in mcqs:
                question = models.QuizQuestions(
                    quiz_id=quiz_id,
                    question_text=mcq['statement'],
                    quest_marks=1,
                    no_of_option=4
                )

                db.add(question)
                await db.commit()
                await db.refresh(question)
                print("Question Created")
                await QuizOptionCrud.create_quiz_option(db, mcq['options'], question.id ,mcq['correct_answer'])

        except Exception as e:
            print(f"in question crud{e}")
            raise

    async def create_quiz_single_question(db: AsyncSession, mcqs, quiz_id):
        try:
            print(mcqs, quiz_id)
            question = models.QuizQuestions(
                quiz_id=quiz_id,
                question_text=mcqs['statement'],
                quest_marks=1,
                no_of_option=4
            )

            db.add(question)
            await db.flush() 

            await db.commit()
            await db.refresh(question)
            print("Question Created")
            await QuizOptionCrud.create_quiz_option(db, mcqs['options'], question.id ,mcqs['correct_answer'])

        except Exception as e:
            print(f"Unhandled Exception: {e}")
            await db.rollback()
            print(f"in question crud{e}")
            raise

    async def get_questions_by_quiz_id(db: AsyncSession, id):
        result = await db.execute(
            select(models.QuizQuestions).where(
                models.QuizQuestions.quiz_id == id,
            )
        )
        
        questions = result.scalars().all()
        return questions
    
    async def get_question_by__id(db: AsyncSession, id):
        result = await db.execute(
            select(models.QuizQuestions).where(
                models.QuizQuestions.id == id,
            )
        )
        
        question = result.scalar_one_or_none()
        return question
    
    async def delete_invalid_questions(db: AsyncSession, quiz_id: int, valid_question_ids: list):
        stmt_delete_options = delete(models.QuestionsOptions).where(
        models.QuestionsOptions.question_id.notin_(valid_question_ids)
        )
        await db.execute(stmt_delete_options)
        stmt = delete(models.QuizQuestions).where(
            models.QuizQuestions.quiz_id == quiz_id,
            models.QuizQuestions.id.notin_(valid_question_ids)
        )
        await db.execute(stmt)
        await db.commit()

    async def update_quiz_question(db: AsyncSession, mcqs):
        try:
            id = None
            question_ids = []
            new_questions = []
            print(mcqs)
            for mcq in mcqs:
                print(f"Mcqs is: {mcq}")
                if mcq.get('quiz_id'):
                    id = mcq.get('quiz_id')
                    if mcq.get('question_id'):
                        question_ids.append(mcq.get('question_id'))
            for mcq in mcqs:
                if mcq.get('question_id'):
                    mcq_ques = await QuizQuestionCrud.get_question_by__id(db, mcq['question_id'])
                    print(mcq_ques.question_text)
                    if mcq_ques:
                        id = mcq_ques.quiz_id
                        mcq_ques.question_text= mcq['statement']
                        await db.commit()
                        await db.refresh(mcq_ques)
                        index = 0
                        for text in mcq['options']:
                            option = await QuizOptionCrud.get_option_by__id(db, mcq['options_ids'][index])
                            option.option_text = text
                            if mcq['correct_answer'] == text:
                                option.option_status = True
                            else:
                                option.option_status = False
                            await db.commit()
                            await db.refresh(option)
                            index = index + 1
                else:
                    print(f"New Mcqs not saved first going for save {mcq} id is {id}")
                    new_questions.append(mcq)
            await QuizQuestionCrud.delete_invalid_questions(db, id, question_ids)
            await QuizQuestionCrud.create_quiz_question(db, new_questions, id)
            return id
        except Exception as e:
            print(f"in question crud{e}")
            raise