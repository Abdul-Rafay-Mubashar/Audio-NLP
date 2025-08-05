from fastapi import FastAPI, Depends, HTTPException, Body, Form, File, UploadFile, Request
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import setting
import shutil, os, re
from docx import Document
import io, gc
import asyncio
from typing import Annotated
from src.db.models import schema, models
from src.db.crud import User
from src.db.crud.Recoder import RecorderCrud
from src.db.crud.NotesQueue import NotesQueueCrud
from src.db.crud.RecordingQueue import RecordingQueueCrud
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
from src.module import quiz_gen, notes_gen_router
from src.db.crud import quiz_crud
from src.sidework import audio_trans, note_gen

from fastapi import BackgroundTasks


router = APIRouter(
    prefix="/notes", 
    tags=["notes"], 
    responses={404: {"description": "Not Found"}}
)

UPLOAD_DIR = rf"C:\Users\Hp\Desktop\FYP\notes"

@router.post("/add",status_code=http_status.HTTP_201_CREATED)
async def generate_notes_from_text(
    background_tasks: BackgroundTasks,
    course_name: str = Form(...),
    lecture_no: int = Form(...),
    course_section: str = Form(...),
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    try:
        if current_user:
            await NotesQueueCrud.add_notes(db, f"{setting.CURRENT_SEMESTER}-{course_name}-{course_section}", lecture_no, current_user.id)
            recording_no = await RecordingQueueCrud.get_no_of_pending_recordings(db, f"{setting.CURRENT_SEMESTER}-{course_name}-{course_section}", lecture_no)
            if recording_no == 0:
                await NotesQueueCrud.mark_notes_complete(db, f"{setting.CURRENT_SEMESTER}-{course_name}-{course_section}", lecture_no)

            if not note_gen.status:
                note_gen.status = True
                

            return {
                "message": "Notes added to queue. You'll receive an email when notes processing is complete."
            }
        else:
            print(f"NoteRouter -->generate_quiz_from_audio: User not found")
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"NoteRouter -->generate_quiz_from_audio: Internal server error {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error"
        )




@router.post("/getcoursenotes",status_code=http_status.HTTP_201_CREATED)
async def generate_notes_from_course_id(
    data: schema.CourseIdSchema,
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    try:
        if current_user:
            print(data.course_id)
            notes = await NotesCrud.get_notes_by_course_id(db, data.course_id)
            return notes

    except Exception as e:
        pass


@router.post("/getnote",status_code=http_status.HTTP_200_OK)
async def generate_notes_from_course_id(
    request:Request,
    data: schema.NotesIdSchema,
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    try:
        if current_user:
            print(data.note_id)
            notes = await NotesCrud.get_notes_by_id(db, data.note_id)
            file_name = os.path.basename(notes.notes_file_path)

            if file_name.lower().endswith('.pdf'):
                word_file_name = file_name[:-4] + '.docx'
                notes_gen_router.save_text_to_word(notes.notes_text, os.path.join(UPLOAD_DIR,"notes_"+word_file_name))
                notes_gen_router.convert_docx_to_pdf(os.path.join(UPLOAD_DIR,"notes_"+word_file_name), os.path.join(UPLOAD_DIR,"notes_"+file_name))




                base_url = str(request.base_url)  # e.g., http://localhost:8000/

            # Build URL
                pdf_url = f"{base_url}notes/notes_{file_name}"

                word_url = f"{base_url}notes/notes_{word_file_name}"
            
                match = re.search(r'_([0-9]+)(?=\.\w+$)', file_name)
                last_number = match.group(1) if match else None
                course_parts = notes.course_id.split('-')
                name = course_parts[1] if len(course_parts) > 1 else None
                sec = course_parts[2] if len(course_parts) > 2 else None
                response =  {
                        "notes_id": notes.id,
                        "pdf_url": pdf_url,
                        "word_url": word_url,
                        "last_number": last_number,
                        "course_name": name,
                        "course_section": sec,
                        "notes_name":notes.notes_file_path
                }
                print(response)
                return response

    except Exception as e:
        print(e)
        pass


@router.post("/edit/upload", status_code=http_status.HTTP_200_OK)
async def upload_file(
    file: UploadFile = File(...),
    file_name: str = Form(...),     
    id: int = Form(...),     

    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db),

):
    try:
        if current_user:
            if not file.filename.lower().endswith('.docx'):
                return {"error": "Please upload a DOCX file."}

            # Save uploaded file directly to disk
            file_location = os.path.join(UPLOAD_DIR, file_name)
            file_pdf = file_name[:-4] + '.docx'
            file_pdf_location = os.path.join(UPLOAD_DIR, file_pdf)
            print(file_location, file_name, file_pdf, file_pdf_location)
            # temp_docx_file = os.path.join(UPLOAD_DIR,f"notes_{file_pdf}")
            # temp_pdf_file = os.path.join(UPLOAD_DIR,f"notes_{file_name}")

            # os.remove(os.path.join(UPLOAD_DIR, ))
            if os.path.exists(file_location):
                os.remove(file_location)
                # os.remove(temp_docx_file)

                print(f"Word file deleted at {file_location}")

            if os.path.exists(file_pdf_location):
                os.remove(file_pdf_location)
                # os.remove(temp_pdf_file)

                print(f"pdf file deleted at {file_pdf_location}")
            print(file_location, file_pdf_location)
            with open(file_pdf_location, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            notes_gen_router.convert_docx_to_pdf(file_pdf_location, file_location)

            doc = Document(file_pdf_location)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)

            text_content = "\n".join(full_text)

            await NotesCrud.update_note_text_by_id(db, id, text_content)
            # ➜ Close UploadFile Streams
            await file.close()
            file.file.close()




            return {"message": "File are deleted sucessfully"}

    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))