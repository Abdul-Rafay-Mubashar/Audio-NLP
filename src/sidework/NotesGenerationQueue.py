import setting, os, asyncio

from ..db.crud.Recoder import RecorderCrud
from ..db.crud.Notes import NotesCrud
from ..db.crud.NotesQueue import NotesQueueCrud
from ..db.crud.User import UserCrud
from ..db.crud.Teacher import TeacherCrud


from ..db.models import schema
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..module import notes_gen


class NotesQueue:

    def __init__(self,):
        self.notes_list: list = []
        self.status = None
        self.path = rf"C:\Users\Hp\Desktop\FYP\notes"

    async def update_to_complete_notes_db(self, db: AsyncSession, course_name: str, course_section: str, lecture_no: int):
        recording = f"{setting.CURRENT_SEMESTER}-{course_name}-{course_section}"
        update_recording = await RecorderCrud.change_status_to_complete_recording(db, recording, lecture_no)


    async def update_to_complete_note_queue(self, course_name: str, course_section: str, lecture_no: int):
        from ..sidework import audio_trans
        recordings = audio_trans.recording_list
        count = 0
        for recording in recordings:
            if (recording["course-name"] == course_name and recording["course-section"] == course_section) and recording['lecture-no'] == lecture_no:
                recording['status'] = 'COMPLETED'
                count = count + 1
        return count


    async def append_text_for_note_in_queue(self, recordings: List[schema.RecorderCreate]):
        text = ''
        for recording in recordings:
            text = text + recording.lecture_text
        
        return text

        
    async def notes_queue_processing(self, db):
        while True:
            try:
                notes_count = await NotesQueueCrud.get_total_notes_count(db)
                if notes_count == 0:
                    print(f"Notes count pending in Queue is {notes_count} so temenatiing the process")
                    self.status = None
                    break
                notes = await NotesQueueCrud.get_first_note(db)
                if notes:
                    print(f"Notes found next from queue is {notes.id}")
                    recordings = await RecorderCrud.get_recordings_of_lecture(db, notes.course_id, notes.lecture_no)
                    print(f"totel recording found for note_id:  {notes.id} is {len(recordings)}")
                    complete_lecture = await self.append_text_for_note_in_queue(recordings)
                    print(f"Text form {len(recordings)} recording is: {complete_lecture}")
                    note_text = notes_gen.generate_notes(complete_lecture)
                    print(note_text)
                    notes_gen.save_text_to_word(note_text, os.path.join(self.path, notes.course_id+'_'+str(notes.lecture_no)+'.docx'))
                    notes_gen.convert_docx_to_pdf(os.path.join(self.path, notes.course_id+'_'+str(notes.lecture_no)+'.docx'),os.path.join(self.path, notes.course_id+'_'+str(notes.lecture_no)+'.pdf'))
                    print(f"PDF is created for notes_id: {notes.id}")
                    await NotesCrud.create_notes(db, notes.course_id, notes.lecture_no, os.path.join(self.path, notes.course_id+'_'+str(notes.lecture_no)+'.pdf'), note_text)
                    await NotesQueueCrud.delete_notes(db, notes)
                    user = await TeacherCrud.get_teacher_by_id(db, notes.user_id)
                    from ..sidework import email_sender
                    await email_sender.send_notes_notification(notes.course_id, notes.lecture_no, user.email, user.user_name, os.path.join(self.path, notes.course_id+'_'+str(notes.lecture_no)+'.pdf'))
                else: 
                    print(f"Notes didnot found in queue so termenating process ")
                    self.status = None
                    break

            except Exception as e:
                print(f"Notes any notes didnot found in queue so termenating process {str(e)}")
                self.status = None
                break

