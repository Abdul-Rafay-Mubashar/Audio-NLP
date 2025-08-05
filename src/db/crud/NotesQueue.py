import re, setting
from datetime import datetime
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func

from ..models import models

class NotesQueueCrud:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_notes(db: AsyncSession, course_id, lecture_no, id, recording=None):
        db_notes = models.NotesQueue(
            user_id = id,
            lecture_status = "COMPLETE",
            course_id = course_id,
            lecture_no = lecture_no,
            recordings_text = recording,
            date = datetime.now().replace(microsecond=0)
        )
        
        db.add(db_notes)
        await db.commit()
        await db.refresh(db_notes)
        return db_notes
    

    async def mark_notes_complete(db: AsyncSession, course_id, lecture_no):
        result = await db.execute(
            select(models.NotesQueue).where(
                models.NotesQueue.course_id == course_id,
                models.NotesQueue.lecture_no == lecture_no
            )
        )
        note = result.scalar_one_or_none()

        if note is None:
            print("Note not found")
            return

        note.recording_queue_status = "COMPLETE"
        await db.commit()


    async def delete_notes(db: AsyncSession, lecture):
        result = await db.execute(
            select(models.NotesQueue).where(
                models.NotesQueue.course_id == lecture.course_id,
                models.NotesQueue.lecture_no == lecture.lecture_no
            )
        )
        note = result.scalar_one_or_none()

        if note is None:
            print("Not found")

        await db.delete(note)
        await db.commit()
        print("✅ Note deleted and commit successful.")


    async def get_first_note(db: AsyncSession):
        result = await db.execute(
            select(models.NotesQueue)
            .where(
                models.NotesQueue.lecture_status == 'COMPLETE',
                models.NotesQueue.recording_queue_status == 'COMPLETE'
            )
            .order_by(models.NotesQueue.id.asc())
            .limit(1)
        )
        first_note = result.scalars().first()
        return first_note
    
    async def get_total_notes_count(db: AsyncSession):
        result = await db.execute(select(func.count()).select_from(models.NotesQueue))
        count = result.scalar()
        return count
    
    async def get_notes_by_course_id_lecture_no(db: AsyncSession, course_id, lecture_no):
        result = await db.execute(
            select(models.NotesQueue).where(
                models.NotesQueue.course_id == course_id,
                models.NotesQueue.lecture_no == lecture_no
            )
        )
        note = result.scalar_one_or_none()

        if note is None:
            print("Note in queue not found")
            return None
        
        return note

