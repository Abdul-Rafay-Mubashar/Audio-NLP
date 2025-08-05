from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import setting
from src.db.models import schema, models
from src.db.crud import User
import base64
from jose import jwt
from datetime import datetime
from fastapi_jwt_auth import AuthJWT
from src.db.models import get_db
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from email.message import EmailMessage
from aiosmtplib import SMTP
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from src.db.crud.Teacher import TeacherCrud
from src.db.crud.User import UserCrud
import base64
from datetime import timedelta

from src.sidework import email_sender


router = APIRouter(
    prefix="/teacher", tags=["teacher"], responses={404: {"description": "Not Found"}}
)


@router.post("/addteacher", status_code=http_status.HTTP_201_CREATED)
async def create_teacher(user: schema.User, db: AsyncSession = Depends(get_db)):
    try:
        db_user = await TeacherCrud.get_teacher_by_email(db, user.email)
        if db_user:
            print(f"TeacherRouter -->create_user: User {user.email} is already registered with this email")
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        db_user = await TeacherCrud.create_teacher(db, user)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        await email_sender.send_activation_link_email(db_user.email, db_user.id, True)

        content = {
            "message": "Teacher created successfully. Please check your email activation.",
        }
        print(f"TeacherRouter -->create_user: User with email {user.email} is created sucessfully")
        return content
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"TeacherRouter -->create_user: Internal server error {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error"
        )


@router.get("/activate/{id}")
async def activate_teacher(
    id: str, Authorize: AuthJWT = Depends(), db: AsyncSession = Depends(get_db)
):
    try:
        decoded_id = email_sender.decode_id(id)
        db_user = await TeacherCrud.get_teacher_by_id(db, str(decoded_id))
        if not db_user:
            print(f"TeacherRouter -->activate_user: User with id {decoded_id} is not registered")

            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="Email not found"
            )
        db_user.is_active = True
        await db.commit()
        await db.refresh(db_user)
    except HTTPException as http_exc:
        raise http_exc 

    except Exception as e:
        print(f"TeacherRouter -->activate-user: Internal server error {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/login")
async def teacher_login(
    user: schema.AuthUser,
    Authorize: AuthJWT = Depends(),
    db: AsyncSession = Depends(get_db),
):
    try:
        db_user = await TeacherCrud.get_teacher_by_email(db, user.email)

        if db_user is None or db_user.is_active == False:
            print(f"TeacherRouter -->teacher_login: Teacher with email {user.email} is not registered")
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )

        if db_user.is_admin == False:
            print(f"TeacherRouter -->teacher_login: Teacher with email {user.email} is trying to access student portal")
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )

        if user.password != db_user.password:
            print(f"TeacherRouter -->teacher_login: Teacher entered in valid password for email {user.email}")

            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Wrong email or password",
            )
        print(f"TeacherRouter -->teacher_login: Teacher {user.email} login sucessfully")
        access_token = Authorize.create_access_token(subject=db_user.email,expires_time=timedelta(hours=24))

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"TeacherRouter -->teacher_login: Internal server error {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error",
        )

    return {"access_token": access_token}

@router.get("/getteacherbyJWT")
async def get_teacher_by_jwt(
    current_user: User = Depends(UserCrud.get_current_user_from_token),
    db: AsyncSession = Depends(get_db),

):
    if current_user:
        return current_user
