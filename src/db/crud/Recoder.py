from src.db.models import models, schema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from fastapi_jwt_auth import AuthJWT
from src.db.models import get_db
import setting
from datetime import datetime


from fastapi import APIRouter, Depends, HTTPException, status as http_status


class RecorderCrud:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_recording(db: AsyncSession, data, audio_text, language):

        db_recorder = models.Recorder(
            user_id=data.user_id,
            course_id= data.course_id,
            lecture_no=data.lecture_no,
            lecture_text=audio_text,
            status=data.recordings_status,
            text_language=language,
            date=datetime.now().replace(microsecond=0)
        )
        db.add(db_recorder)
        await db.commit()
        await db.refresh(db_recorder)
        return db_recorder
    
    async def change_status_to_complete_recording(db:AsyncSession, course_id: str, lecture_no: int):
        print(course_id,lecture_no)
        result = await db.execute(
            select(models.Recorder).where(
                models.Recorder.course_id == course_id, models.Recorder.lecture_no == lecture_no
            )
        )
        if result:
            recorders = result.scalars().all()
            for recorder in recorders:
                recorder.status = "COMPLETED"

        await db.commit()
        return True

    async def get_recordings_of_lecture(db:AsyncSession, course_id: str, lecture_no: int):
        result = await db.execute(
            select(models.Recorder).where(
                models.Recorder.course_id == course_id, models.Recorder.lecture_no == lecture_no
            )
        )
        recordings = result.scalars().all()
        return recordings
    
    async def get_lect_info_for_new_lect(db: AsyncSession, course_name: str, course_sec: str,):
        # Update the retry field by +1
        course_id = f"{setting.CURRENT_SEMESTER}-{course_name}-{course_sec}"
        result = await db.execute(
            select(models.Recorder)
            .where(
                models.Recorder.course_id == course_id,
            )
        )
        rows = result.scalars().all()

        if not rows:
            return None

        max_lecture_no = max(row.lecture_no for row in rows if row.lecture_no is not None)
        return max_lecture_no
