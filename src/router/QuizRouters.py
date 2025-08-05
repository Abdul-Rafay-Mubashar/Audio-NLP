from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import setting
import asyncio
from typing import Annotated
from src.db.models import schema, models
from src.db.crud import User
from src.db.crud.Quiz import QuizCrud
from src.db.crud.StudentAnswer import AnswerCrud
from src.db.crud.StudentsMarks import MarksCrud
from datetime import datetime


from src.db.crud.TeacherCourse import TeacherCourseCrud
from src.db.crud.Notes import NotesCrud
from src.module.QuizGenration import QuizGenerator
from fastapi_jwt_auth import AuthJWT
from src.db.models import get_db
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from email.message import EmailMessage
from aiosmtplib import SMTP
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from src.db.crud.User import UserCrud
from src.module import quiz_gen
from src.db.crud import quiz_crud
from src.sidework import email_sender


router = APIRouter(
    prefix="/quiz", 
    tags=["quiz"], 
    responses={404: {"description": "Not Found"}}
)

# TODO Add User Athentication that is_admin is True or not
@router.post("/genrates")
async def genrate_quiz(
    req: schema.McqsSyllabus,
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db),

):
    if current_user:
        paths = []
        for id in req.path_id:
            note = await NotesCrud.get_notes_by_id(db, id)
            paths.append(note.notes_file_path)
        print("paths are: ",paths, "need to generate: ", req.tol_no + 5)
        quiz = await asyncio.to_thread(quiz_gen.genrate_quiz, paths, req.tol_no + 5)
        formated_quiz = quiz_crud.praser(quiz)
        return {"formated_quiz": formated_quiz}
        # return {"quiz": quiz}


@router.post("/create")
async def create_quiz_endpoint(
    quiz_data: dict = Body(...),
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db)):
    try:
        if current_user:
            print(quiz_data)
            quiz = await QuizCrud.create_quiz(db, quiz_data)
            student_ids = await TeacherCourseCrud.get_users_from_course_id(db, quiz_data['quizInfo']['course_id'])

            emails = await UserCrud.get_user_emails_from_course_id(db, student_ids)
            retry = 3
            while True:
                if retry == 0:
                    break
                try:
                    await email_sender.send_new_quiz_notification(quiz_data['quizInfo']['course_id'], quiz.date, quiz.time, emails)
                    break
                except:
                    retry = retry - 1

        return {"message": "Quiz created successfully"}
    except Exception as e:
        print("❌ Error creating quiz:", e)

        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/get-quiz") 
async def get_quiz_by_id(
    quiz_data: dict = Body(...),
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db)):
    try:
        if current_user:
            print(quiz_data)
            mcqs, quizInfo = await QuizCrud.get_quiz_by_id(db, quiz_data['id'])
            
            # quiz = await create_quiz(db, quiz_data)
        return {"mcqs": mcqs, "quiz_info": quizInfo}
    except Exception as e:
        print("❌ Error creating quiz:", e)

        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/get-quiz-exam") 
async def get_quiz_by_id_for_exam(
    quiz_data: dict = Body(...),
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db)):
    try:
        if current_user:
            print(quiz_data)
            mcqs, quizInfo = await QuizCrud.get_quiz_by_id(db, quiz_data['id'])
            print(f"Lenth of mcqs is {mcqs}")
            marks = await MarksCrud.get_marks_bystudent_id_quiz_id(db, current_user.id, quiz_data['id'])
            if marks:
                raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="You Attempted Your Quiz")

            # quiz = await create_quiz(db, quiz_data)
        return {"mcqs": mcqs, "quiz_info": quizInfo}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print("❌ Error creating quiz:", e)

        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-quiz")
async def create_quiz_endpoint(
    quiz_data: dict = Body(...),
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db)):
    try:
        if current_user:
            print(quiz_data)
            quiz = await QuizCrud.update_quiz(db, quiz_data)
            student_ids = await TeacherCourseCrud.get_users_from_course_id(db, quiz.course_id)

            emails = await UserCrud.get_user_emails_from_course_id(db, student_ids)
            retry = 3
            while True:
                if retry == 0:
                    break
                try:
                    await email_sender.send_update_quiz_notification(quiz.course_id, quiz.date, quiz.time, emails)

                    break
                except:
                    retry = retry - 1
        mcqs, quizInfo = await QuizCrud.get_quiz_by_id(db, quiz.id)
            
            # quiz = await create_quiz(db, quiz_data)
        return {"mcqs": mcqs, "quiz_info": quizInfo}
            # quiz = await create_quiz(db, quiz_data)
    except Exception as e:
        print("❌ Error creating quiz:", e)

        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get-course-quizes")
async def get_quizes_endpoint(
    quiz_data: dict = Body(...),
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db)):
    try:
        if current_user:

            quzzies = await QuizCrud.get_quizes_course_id(db, quiz_data['course_id'])
        return quzzies
    except Exception as e:
        print("❌ Error creating quiz:", e)

        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/get-course-quizes-pending")
async def get_quizes_endpoint(
    quiz_data: dict = Body(...),
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db)):
    try:
        if current_user:

            quzzies = await QuizCrud.get_quizes_course_id_status_pending(db, quiz_data['course_id'])
        return quzzies
    except Exception as e:
        print("❌ Error creating quiz:", e)

        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/save-student-awnser")
async def get_save_answers(
    quiz_data: dict = Body(...),
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db)):
    try:
        if current_user:
            course_id = await QuizCrud.get_course_id_by_quiz_id(db, quiz_data['mcqs'][0]['quiz_id'])

            obtained_marks = 0
            quiz = await QuizCrud.get_single_quiz_by_id(db, quiz_data['mcqs'][0]['quiz_id'])


            if quiz.status == "COMPLETE":
                # await MarksCrud.create_marks(db, course_id, current_user.id, len(quiz_data['mcqs']), 0, quiz_data['mcqs'][0]['quiz_id'])
                print("Marked zero becuase time exceded")
                return

            for mcq in quiz_data['mcqs']:
                answer = await AnswerCrud.create_awnser(db, mcq, course_id, current_user.id)
                if answer:
                    obtained_marks += 1
            await MarksCrud.create_marks(db, course_id, current_user.id, len(quiz_data['mcqs']), obtained_marks, quiz_data['mcqs'][0]['quiz_id'])
    except Exception as e:
        print("❌ Error creating quiz:", e,current_user.id)

        raise HTTPException(status_code=500, detail=str(e))
    



@router.post("/get-quiz-all")
async def get_quizes_endpoint(
    quiz_data: dict = Body(...),
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db)):
    try:
        if current_user:
            print(quiz_data)
            marks = await MarksCrud.get_marks_with_usernames_by_quiz_id(db, quiz_data['quiz_id'])

            return marks

    except Exception as e:
        print("❌ Error creating quiz:", e)

        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/get-quiz-all-course")
async def get_quizes_endpoint(
    quiz_data: dict = Body(...),
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db)):
    try:
        if current_user:
            print(quiz_data)
            marks = await MarksCrud.get_quiz_with_course_id_by_quiz_id_with_marks(db, quiz_data['course_id'], current_user.id)

            return marks

    except Exception as e:
        print("❌ Error creating quiz:", e)

        raise HTTPException(status_code=500, detail=str(e))