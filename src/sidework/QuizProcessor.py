import setting, os, asyncio
from datetime import datetime
from datetime import datetime, timedelta, date

from ..db.crud.Recoder import RecorderCrud
from ..db.crud.Notes import NotesCrud
from ..db.crud.NotesQueue import NotesQueueCrud
from ..db.crud.User import UserCrud
from ..db.crud.StudentsMarks import MarksCrud

from ..db.crud.Teacher import TeacherCrud
from ..db.crud.TeacherCourse import TeacherCourseCrud

from ..db.crud.Quiz import QuizCrud


from ..db.models import schema
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..module import notes_gen


class QuizProcessor:

    def __init__(self):
        pass

    async def quiz_processing(self, db):
        print("Quiz Processing is running")
        in_progress_id = []
        complete_id = []

        quiz_pending_status = await QuizCrud.get_quiz_by_status_pending_in_progress_and_day(db)
        print(f"{len(quiz_pending_status)} quizzes found with PENDING or IN_PROGRESS status")

        now = datetime.now()

        for quiz in quiz_pending_status:
            # quiz.time is a datetime.time object (e.g. 15:00:00)
            start_datetime = datetime.combine(date.today(), quiz.time)  # convert to full datetime

            total_questions = int(quiz.total_marks)
            duration_minutes = total_questions + 2

            end_datetime = start_datetime + timedelta(minutes=duration_minutes)

            print(f"Start Time: {start_datetime.time()}")
            print(f"End Time: {end_datetime.time()}")
            print(f"Current Time: {now.time()}")

            if start_datetime <= now < end_datetime:
                if quiz.status == "IN_PROGRESS":
                    continue
                await QuizCrud.update_quiz_status_in_progress_by_id(db, quiz.id)
                in_progress_id.append(quiz.id)
                print(f"Quiz with id {quiz.id} updated with status IN_PROGRESS")

            elif now >= end_datetime:
                await QuizCrud.update_quiz_status_complete_by_id(db, quiz.id)
                complete_id.append(quiz.id)
                print(f"Quiz with id {quiz.id} updated with status COMPLETE")

                user_ids = await TeacherCourseCrud.get_users_from_course_id(db, quiz.course_id)
                for id in user_ids:
                    marks = await MarksCrud.get_marks_bystudent_id_quiz_id(db, id, quiz.id)
                    if not marks:
                        print(f"ID NO : {id} didnot give the quiz so marked zero")
                        await MarksCrud.create_marks(db, quiz.course_id, id, quiz.total_marks, 0, quiz.id)

        print(f"Quizzes updated to IN_PROGRESS: {in_progress_id}")
        print(f"Quizzes updated to COMPLETE: {complete_id}")




