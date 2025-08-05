from src.db.crud import Quiz, User, Teacher, Recoder
from sqlalchemy.ext.asyncio import AsyncSession

quiz_crud = Quiz.QuizCrud(session=AsyncSession)
user_crud = User.UserCrud(session=AsyncSession)
teacher_crud = Teacher.TeacherCrud(session=AsyncSession)
recorder_crud = Recoder.RecorderCrud(session=AsyncSession)



