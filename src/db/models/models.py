from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, Time, DATETIME
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import declarative_base, relationship
import setting

Base = declarative_base()


from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    is_active = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    user_name = Column(String(100), nullable=True)

    teacher_courses = relationship("TeacherCourse", back_populates="student")
    recordings = relationship(
        "Recorder", back_populates="user", cascade="all, delete-orphan"
    )


class Course(Base):
    __tablename__ = "courses"
    id = Column(String(255), primary_key=True)   # it should be course section with semester with course name code like(S2022,F2021 etcs)
    name = Column(String(255))
    section = Column(String(255),)
    semester = Column(String(255), default=setting.CURRENT_SEMESTER)

    teacher_courses = relationship("TeacherCourse", back_populates="course")
    quizzes = relationship("Quiz", back_populates="course")
    notes = relationship("Notes", back_populates="course", cascade="all, delete-orphan")
    recordings = relationship(
        "Recorder", back_populates="course", cascade="all, delete-orphan"
    )


class TeacherCourse(Base):
    __tablename__ = "teacher_courses"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(String(255), ForeignKey("courses.id"))

    student = relationship("User", back_populates="teacher_courses")
    course = relationship("Course", back_populates="teacher_courses")


class Quiz(Base):
    __tablename__ = "quiz"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String(255), ForeignKey("courses.id"))
    total_marks = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    status = Column(String(255), nullable=False)

    course = relationship("Course", back_populates="quizzes")
    questions = relationship(
        "QuizQuestions", back_populates="quiz", cascade="all, delete-orphan"
    )


class QuizQuestions(Base):
    __tablename__ = "quiz_questions"
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quiz.id"))
    question_text = Column(String(255), nullable=False)
    quest_marks = Column(Integer, nullable=False,)
    no_of_option = Column(Integer, nullable=False)

    quiz = relationship("Quiz", back_populates="questions")
    options = relationship(
        "QuestionsOptions", back_populates="question", cascade="all, delete-orphan"
    )


class QuestionsOptions(Base):
    __tablename__ = "questions_options"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("quiz_questions.id"))
    option_text = Column(String(255), nullable=False)
    option_status = Column(Boolean, nullable=False, default=False)

    question = relationship("QuizQuestions", back_populates="options")

class StudentAnswer(Base):
    __tablename__ = "student_answer"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String(255))
    question_id = Column(Integer)
    quiz_id = Column(Integer)
    student_id = Column(Integer)

    answer_text = Column(String(255), nullable=False)
    correct_answer = Column(String(255), nullable=False)


class StudentMark(Base):
    __tablename__ = "student_marks"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String(255))
    quiz_id = Column(Integer)
    student_id = Column(Integer)
    total_marks = Column(Integer, default=0)
    obtained_marks = Column(Integer)


class Notes(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String(255), ForeignKey("courses.id"))
    topic_name = Column(String(255), nullable=False, default="OK")
    lecture_no = Column(Integer, nullable=True)
    notes_file_path = Column(String(255), nullable=False)
    notes_text = Column(LONGTEXT, nullable=False)

    date = Column(DATETIME, nullable=False)

    course = relationship("Course", back_populates="notes")


class Recorder(Base):
    __tablename__ = "record"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(String(255), ForeignKey("courses.id"), nullable=True)
    lecture_no = Column(Integer, nullable=False)
    lecture_text = Column(LONGTEXT, nullable=False)
    text_language = Column(String(255), nullable=True)
    status = Column(String(255), nullable=False)
    date = Column(DATETIME, nullable=False)

    user = relationship("User", back_populates="recordings")
    course = relationship("Course", back_populates="recordings")


class NotesQueue(Base):
    __tablename__ = "notesqueue"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(String(255))
    lecture_no = Column(Integer, nullable=True)
    recordings_text = Column(LONGTEXT, nullable=True)
    recording_queue_status = Column(String(255), default="PENDING")
    lecture_status = Column(String(255), default="PENDING")
    date = Column(Date, nullable=False)


class RecordingQueue(Base):
    __tablename__ = "recordingqueue"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(String(255))
    lecture_no = Column(Integer, nullable=True)
    filename = Column(String(255), nullable=False)
    recordings_status = Column(LONGTEXT, nullable=False)
    retry = Column(Integer, default=0)
    date = Column(Date, nullable=False)
