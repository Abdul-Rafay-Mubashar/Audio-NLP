import setting, time, asyncio
from src.sidework.ForgetPasswordQueue import ForgetPassQueue
from src.sidework.UserEmail import UserEmail
from src.sidework.AudioTranslationQueue import AudioTransQueue
from src.sidework.NotesGenerationQueue import NotesQueue
from src.sidework.QuizProcessor import QuizProcessor
from src.db.crud.NotesQueue import NotesQueueCrud
from src.db.models import get_db
from fastapi import APIRouter, Depends, HTTPException, status as http_status


audio_queue_status = None
notes_queue_status = None

db = get_db()

forget_pass = ForgetPassQueue()
email_sender = UserEmail()
audio_trans = AudioTransQueue() 
note_gen = NotesQueue()
note_gen_router = NotesQueue()
quiz_porcess = QuizProcessor()

async def check_audio_queue():
    while True:
        if audio_trans.status == True:
            audio_queue_status = True
            async for db in get_db():
                await audio_trans.audio_queue_processing(db)
        else:
            audio_queue_status = None
        print(f"Status of audio_trans is {audio_trans.status} and of audio_queue_status is {audio_queue_status}")
        await asyncio.sleep(30)


async def check_notes_queue():
    while True:
        if note_gen.status == True:
            note_queue_status = True
            async for db in get_db():
                await note_gen.notes_queue_processing(db)
                
        else:
            note_queue_status = None
        print(f"Status of note gen is {note_gen.status} and of note_queue_status is {note_queue_status}")
        await asyncio.sleep(30)


async def check_notes_status_in_db():
    while True:
        print("Checking in function: check_notes_status_in_db()")

        if note_gen.status == None:
            async for db in get_db():
                notes = await NotesQueueCrud.get_first_note(db)              
                if notes:
                    note_gen.status = True
                    print(f"Notes processor activated because notes with id {notes.id} is present in queue and it was terminated due to error")
                else:
                    print(f"No notes found in queue so note_gen sttus is {note_gen.status}")
        await asyncio.sleep(30)


async def run_quiz_processor():
    while True:
        async for db in get_db():
            await quiz_porcess.quiz_processing(db)
        await asyncio.sleep(30)
