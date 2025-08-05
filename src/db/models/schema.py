from typing import List, Union
from pydantic import BaseModel
from datetime import date



class User(BaseModel):
    first_name : str
    last_name : str
    is_admin : bool = False
    email : str
    password : str

class AuthUser(BaseModel):
    email : str
    password : str

class UserNewPassword(BaseModel):
    email : str
    newPassword : str

class ForgetPasswordRequest(BaseModel):
    email: str

class ForgetPasswordOTPVerfy(BaseModel):
    email: str
    otp: int

class McqsSyllabus(BaseModel):
    tol_no : int
    path_id: List[int]

class RecorderCreate(BaseModel):
    course_name: str
    lecture_no: int
    course_section: str

class QuizIdRequest(BaseModel):
    quiz_id: int





class RecorderCreate(BaseModel):
    user_id: int
    course_id: str | None
    lecture_no: int
    lecture_text: str
    text_language: str
    status: str
    date: date

class CourseOut(BaseModel):
    id: str
    name: str
    section: str
    semester: str

class CourseIdSchema(BaseModel):
    course_id: str

class NotesIdSchema(BaseModel):
    note_id: int