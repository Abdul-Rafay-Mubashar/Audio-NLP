from fastapi import FastAPI, Depends, HTTPException, Body, Form, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import setting
import shutil, os
import asyncio
from typing import Annotated, List
from src.db.models import schema, models
from src.db.crud import User
from src.db.crud.Recoder import RecorderCrud
from src.db.crud.NotesQueue import NotesQueueCrud
from src.db.crud.RecordingQueue import RecordingQueueCrud
from src.db.crud.TeacherCourse import TeacherCourseCrud
from src.db.crud.Courses import CourseCrud

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
from src.sidework import audio_trans, note_gen

from fastapi import BackgroundTasks


router = APIRouter(
    prefix="/courses", 
    tags=["courses"], 
    responses={404: {"description": "Not Found"}}
)



@router.get("/getusercourses",status_code=http_status.HTTP_200_OK)
async def get_courses_from_user_id(
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    try:
        if current_user:
            courses = await TeacherCourseCrud.get_course_by_user_id(db, current_user.id)
            for course in courses:
                course_id: str = course.course_id
                name = course_id.split('-')
                course.course_id = name[1]
            
                # Deduplicate by course_id (which now holds only the name)
            unique_courses = {}
            for course in courses:
                if course.course_id not in unique_courses:
                    unique_courses[course.course_id] = course

            result = list(unique_courses.values())
            return result if result else []



    except Exception as e:
        print(f"TeacherCourseRouter -->get_courses_from_user_id: Internal server error {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error"
        )

@router.get("/getusercoursessections",status_code=http_status.HTTP_200_OK)
async def get_section_from_user_id_and_name(
    name:str,
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    try:
        if current_user:
            sections = await TeacherCourseCrud.get_section_by_user_id_course_name(db, current_user.id, name)
            for section in sections:
                course_id: str = section.course_id
                name = course_id.split('-')
                section.course_id = name[2]
            print(sections)
            return sections
                

    except Exception as e:
        print(f"TeacherCourseRouter -->get_courses_from_user_id: Internal server error {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error"
        )
    

@router.get("/getcoursesbyuser", status_code=http_status.HTTP_200_OK)
async def get_courses_from_user_id(
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    try:
        if current_user:
            all_courses = []
            courses = await TeacherCourseCrud.get_course_by_user_id(db, current_user.id)
            for course in courses:
                one_course = await CourseCrud.get_course_by_course_id(db, course.course_id)
                all_courses.append(one_course)
            
            return all_courses
        
    except Exception as e:
        print(f"TeacherCourseRouter -->get_courses_from_user_id: Internal server error {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error"
        )