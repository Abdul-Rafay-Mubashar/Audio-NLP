import re, setting
from datetime import datetime
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import models
from sqlalchemy import select, update, delete, func


class NotesCrud:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_notes(db: AsyncSession, course_id, lecture_no, path, text):
        db_notes = models.Notes(
            course_id= course_id,
            lecture_no=lecture_no,
            notes_file_path=path, 
            notes_text = text,
            date=datetime.now().replace(microsecond=0)
        )
        
        db.add(db_notes)
        await db.commit()
        await db.refresh(db_notes)
        return db_notes
    
    async def get_notes_by_course_id(db: AsyncSession, course_id):
        result = await db.execute(
            select(models.Notes).where(
                models.Notes.course_id == course_id,
            )
        )
        
        notes = result.scalars().all()
        return notes
    
    async def get_notes_by_id(db: AsyncSession, id):
        result = await db.execute(
            select(models.Notes).where(
                models.Notes.id == id,
            )
        )
        
        notes = result.scalar_one_or_none()
        return notes


    async def update_note_text_by_id(db: AsyncSession, id, text):
        result = await db.execute(
            select(models.Notes).where(
                models.Notes.id == id,
            )
        )
        
        notes = result.scalar_one_or_none()
        if not notes:
            return None  

        notes.notes_text = text  

        await db.commit()  
        await db.refresh(notes) 
                
        return notes