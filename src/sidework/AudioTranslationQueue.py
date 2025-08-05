import os
from src.db.models import schema
from src.module import notes_gen
from src.db.crud.Recoder import RecorderCrud
from src.db.crud.NotesQueue import NotesQueueCrud
from src.db.crud.RecordingQueue import RecordingQueueCrud


from src.db.models import get_db
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession




class AudioTransQueue:

    def __init__(self,):
        self.recording_list: list = []
        self.path = rf"C:\Users\Hp\Desktop\FYP\recording"
        self.status = None

    def append_recording_to_queue(
        self,
        course_section: str,
        course_name: str,
        lecture_no: int,
        filename: str,
        current_user: schema.User
    ):
        recording = {
            "course-name": course_name,
            "lecture-no": lecture_no,
            "course-section": course_section,
            "file-name": filename,
            "status": "PENDING",
            "user": current_user
        }
        self.recording_list.insert(0, recording)
        print(f"AudioTranslationQueue -->append_to_queue: {filename} added for audio translation. ")

    def append_recording_preprocessing(self, prefix):
        try:
            matched_files = [
                f for f in os.listdir(self.path)
                if os.path.isfile(os.path.join(self.path, f)) and f.startswith(prefix)
            ]
            print(matched_files)
            if len(matched_files) == 0:
                return 0
            last_file = matched_files[-1]
            last_file_name_split = last_file.split("_")
            split_by_point = last_file_name_split[-1].split('.')
            print(last_file_name_split[-1])
            return int(split_by_point[0])

        except FileNotFoundError:
            print(f"Folder not found: {prefix}")
            return 0

    def audio_get_next(self):
        return self.recording_list[-1] if self.recording_list else None
    
    def check_recording_with_same_lecture_no_and_course_id(self, course_id: str, lecture_no: int):
        for recording in self.recording_list:
            if (recording['course-id'] == course_id and recording['lecture-no'] == lecture_no) and recording["status"] == "COMPLETE":
                return True
        return None

    async def audio_queue_processing(self, db: AsyncSession = Depends(get_db),):
        while True:
            try:
                file_detail = await RecordingQueueCrud.get_first_recording(db)
                if file_detail:
                    audio_text, language = notes_gen.audio_processor(file_detail.filename)
                    print(f"audio_text and language are both : {audio_text}, {language} ")
                    if not audio_text and not language:
                        raise ValueError("audio_text and language are both None")
                    recorder = await RecorderCrud.create_recording(db, file_detail, audio_text, language)
                    print("Recording Created")
                    await RecordingQueueCrud.delete_recording(db, file_detail.id)
                    recording_no = await RecordingQueueCrud.get_no_of_pending_recordings(db, file_detail.course_id, file_detail.lecture_no)
                    notes_status_in_queue = await NotesQueueCrud.get_notes_by_course_id_lecture_no(db, file_detail.course_id, file_detail.lecture_no)
                    if not notes_status_in_queue:
                        continue
                    if recording_no == 0 and notes_status_in_queue.lecture_status == "COMPLETE":
                        await NotesQueueCrud.mark_notes_complete(db, file_detail.course_id, file_detail.lecture_no)
                else:
                    totel_no = await RecordingQueueCrud.get_total_recording_count(db)
                    if totel_no == 0:
                        self.status = None
                        break
            except Exception as e:
                if file_detail:
                    if file_detail.retry == 3:
                        await RecordingQueueCrud.delete_recording(db, file_detail.id)
                        # from sidework.UserEmail import UserEmail
                        # course_detail = file_detail.course_id
                        # course_detail = course_detail.split('-')
                        # await UserEmail.send_recording_failed_notification()
                        continue
                    await RecordingQueueCrud.increment_retry_by_id(db, file_detail.id)
                    print(f"Sidework -->AudioTranslationQueue: Error in translation {str(e)}")

    def change_status_to_complete_queue(self, filename):
        pass

