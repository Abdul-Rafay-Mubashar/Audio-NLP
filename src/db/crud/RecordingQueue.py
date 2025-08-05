import re, setting
from datetime import datetime
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func

from ..models import models

class RecordingQueueCrud:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_recording(db: AsyncSession, user_id, course_id, lecture_no, recording, filename):
        db_notes = models.RecordingQueue(
            user_id = user_id,
            course_id = course_id,
            lecture_no = lecture_no,
            recordings_status = recording,
            filename = filename,
            date = datetime.now().replace(microsecond=0)
        )
        
        db.add(db_notes)
        await db.commit()
        await db.refresh(db_notes)
        return db_notes
    
    async def get_first_recording(db: AsyncSession):
        result = await db.execute(select(models.RecordingQueue).order_by(models.RecordingQueue.id.asc()).limit(1))
        first_note = result.scalar_one_or_none()
        return first_note
    
    async def delete_recording(db: AsyncSession, id):
        result = await db.execute(
            select(models.RecordingQueue).where(
                models.RecordingQueue.id == id,
            )
        )
        note = result.scalar_one_or_none()

        if note is None:
            print("Not found")

        await db.delete(note)
        await db.commit()

    async def get_total_recording_count(db: AsyncSession):
        result = await db.execute(select(func.count()).select_from(models.RecordingQueue))
        count = result.scalar()
        return count
    

    async def get_no_of_pending_recordings(db: AsyncSession, course_id: str, lecture_no: int) -> int:
        result = await db.execute(
        select(models.RecordingQueue)
            .where(
                models.RecordingQueue.course_id == course_id,
                models.RecordingQueue.lecture_no == lecture_no
            )
        )
        records = result.scalars().all()
        return len(records)
    
    
    async def increment_retry_by_id(db: AsyncSession, record_id: int):
        # Update the retry field by +1
        stmt = (
            update(models.RecordingQueue)
            .where(models.RecordingQueue.id == record_id)
            .values(retry=models.RecordingQueue.retry + 1)
            .execution_options(synchronize_session="fetch")  # ensures the session is in sync
        )

        await db.execute(stmt)
        await db.commit()

    async def get_lect_info_for_new_lect(db: AsyncSession, course_name: str, course_sec: str,):
        course_id = f"{setting.CURRENT_SEMESTER}-{course_name}-{course_sec}"
        result = await db.execute(
            select(models.RecordingQueue)
            .where(
                models.RecordingQueue.course_id == course_id,
            )
        )
        rows = result.scalars().all()

        if not rows:
            return None

        max_lecture_no = max(row.lecture_no for row in rows if row.lecture_no is not None)
        return max_lecture_no