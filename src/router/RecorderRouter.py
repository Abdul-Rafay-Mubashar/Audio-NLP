from fastapi import FastAPI, Depends, HTTPException, Body, Form, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import setting
import shutil, os
import asyncio
from typing import Annotated
from src.db.models import schema, models
from src.db.crud import User
from src.db.crud.RecordingQueue import RecordingQueueCrud
from src.db.crud.Recoder import RecorderCrud

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
from src.sidework import audio_trans
from fastapi import BackgroundTasks


router = APIRouter(
    prefix="/recorder", 
    tags=["recorder"], 
    responses={404: {"description": "Not Found"}}
)

UPLOAD_DIR = r"C:\Users\Hp\Desktop\FYP\recording"

async def schedule_audio_processing(db, audio_trans):
    await audio_trans.audio_queue_processing(db)

@router.post("/add", status_code=http_status.HTTP_201_CREATED)
async def generate_quiz_from_audio(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),  # <-- uploaded .webm audio file
    course_name: str = Form(...),
    lecture_no: int = Form(...),
    course_section: str = Form(...),
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    try:
        if not current_user:
            print("RecorderRouter -->generate_quiz_from_audio: User not found")
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Generate filename
        filename_prefix = f"{setting.CURRENT_SEMESTER}_{course_name}_{lecture_no}_{course_section}"
        file_no = audio_trans.append_recording_preprocessing(filename_prefix)
        print(file_no)
        filename = f"{filename_prefix}_{file_no + 1}.webm"
        file_path = os.path.join(UPLOAD_DIR, filename)
        course_id = f"{setting.CURRENT_SEMESTER}-{course_name}-{course_section}"
        print(file_path)
        # Save file to disk
        print("Received file:", audio.filename)
        print("Content type:", audio.content_type)

        # audio.file.seek(0)
        # with open(file_path, "wb") as buffer:
        #     shutil.copyfileobj(audio.file, buffer)

        contents = await audio.read()  # 🔥 Only read ONCE
        with open(file_path, "wb") as f:
            f.write(contents)

        print(f"Recording save at {file_path}")
        print("Saved file size:", os.path.getsize(file_path))


        await RecordingQueueCrud.add_recording(db, current_user.id, course_id, lecture_no, "PENDING", filename)
        # Add task to internal queue
        audio_trans.append_recording_to_queue(
            course_section=course_section,
            lecture_no=lecture_no,
            course_name=course_name,
            filename=filename,
            current_user=current_user
        )

        # Start processing task if not already running
        if not audio_trans.status:
            audio_trans.status = True

        # Respond immediately
        return {
            "message": "Recording uploaded. You'll receive an email when processing is complete."
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"RecorderRouter -->generate_quiz_from_audio: Internal server error: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/newlecinfo", status_code=http_status.HTTP_200_OK)
async def get_recording_lect_info_for_new_lect(
    course_name: str,
    course_sec: str,
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    if current_user:
        course_id = f"{setting.CURRENT_SEMESTER}-{course_name}-{course_sec}"
        results = await RecordingQueueCrud.get_lect_info_for_new_lect(db, course_name, course_sec)
        if results:
            return {"last_lec_no":results, "course_id":course_id }
        results = await RecorderCrud.get_lect_info_for_new_lect(db, course_name, course_sec)
        if results:
            return {"last_lec_no":results, "course_id":course_id }
        return {"last_lec_no":0, "course_id":course_id }