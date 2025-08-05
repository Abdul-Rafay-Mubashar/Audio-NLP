from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import setting
from src.db.models import schema, models
from src.db.crud import User
import base64
from fastapi_jwt_auth import AuthJWT
from src.db.models import get_db
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from email.message import EmailMessage
from aiosmtplib import SMTP
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from src.db.crud.User import UserCrud
import base64
from datetime import timedelta
import hmac
import hashlib, random
from src.sidework import forget_pass, email_sender


router = APIRouter(
    prefix="/users", tags=["users"], responses={404: {"description": "Not Found"}}
)


@router.get("/")
async def index():
    return {"message": "Welcome to AI Driven Advanced Medical Platform!"}


@router.post("/login")
async def login(
    user: schema.AuthUser,
    Authorize: AuthJWT = Depends(),
    db: AsyncSession = Depends(get_db),
):
    try:
        db_user = await UserCrud.get_user_by_email(db, user.email)

        if db_user is None or db_user.is_active == False:
            print(f"UserRouter -->login: User with email {user.email} is not registered")
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if db_user.is_admin == True:
            print(f"UserRouter -->login: Student with email {user.email} is trying to access teacher portal")
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.password != db_user.password:
            print(f"UserRouter -->login: User entered in valid password for email {user.email}")

            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Wrong email or password",
            )
        print(f"UserRouter -->login: User {user.email} login sucessfully")
        access_token = Authorize.create_access_token(subject=db_user.email,expires_time=timedelta(hours=24))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"UserRouter -->login: Internal server error {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error",
        )

    return {"access_token": access_token}




@router.post("/adduser", status_code=http_status.HTTP_201_CREATED)
async def create_user(user: schema.User, db: AsyncSession = Depends(get_db)):
    try:
        db_user = await UserCrud.get_user_by_email(db, user.email)
        if db_user:
            print(f"UserRouter -->create_user: User {user.email} is already registered with this email")
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        db_user = await UserCrud.create_user(db, user)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        await email_sender.send_activation_link_email(db_user.email, db_user.id, False)

        content = {
            "message": "User created successfully. Please check your email activation.",
        }
        print(f"UserRouter -->create_user: User with email {user.email} is created sucessfully")
        return content
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"UserRouter -->create_user: Internal server error {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error"
        )


# TODO Render to the login page
@router.get("/activate/{id}")
async def activate_user(
    id: str, Authorize: AuthJWT = Depends(), db: AsyncSession = Depends(get_db)
):
    try:
        decoded_id = email_sender.decode_id(id)
        db_user = await UserCrud.get_user_by_id(db, str(decoded_id))
        if not db_user:
            print(f"UserRouter -->activate_user: User with id {decoded_id} is not registered")

            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="Email not found"
            )
        db_user.is_active = True
        await db.commit()
        await db.refresh(db_user)
    except HTTPException as http_exc:
        raise http_exc 

    except Exception as e:
        print(f"UserRouter -->activate-user: Internal server error {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/forgetpassword/")
async def forget_password(
    data: schema.ForgetPasswordRequest, db: AsyncSession = Depends(get_db)
):
    try:
        db_user = await UserCrud.get_user_by_email(db, data.email.lower())
        if not db_user:
            print(f"UserRouter -->forget_password: User with email {data.email} is not registered")

            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="Email not found"
            )
        otp = email_sender.generate_random_4_digit()
        await email_sender.send_otp_email(db_user.email, otp)
        forget_pass.append_to_queue(str(db_user.email), int(otp))
    except HTTPException as http_exc:
        raise http_exc 

    except Exception as e:
        print(f"UserRouter -->forget_password: Internal server error {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    

@router.post("/verifyforgetpasswordotp/")
async def forget_password_otp_verify(
    data: schema.ForgetPasswordOTPVerfy, db: AsyncSession = Depends(get_db)
):
    try:
        queue_user = forget_pass.get_email_otp_from_queue(data.email)
        if not queue_user:
            print(f"UserRouter -->forget_password_otp_verify: User with email {data.email} is not requested for forget password")

            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="Email not found"
            )
        if queue_user['otp'] == data.otp:
            forget_pass.pop_from_queue(data.email)
            return True
        else:
            print(f"UserRouter -->forget_password_otp_verify: User with email {data.email} entered wrong OTP: {data.otp} real one is: {queue_user['otp']}")            
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP"
            )
    except HTTPException as http_exc:
        raise http_exc 

    except Exception as e:
        print(f"UserRouter -->forget_password_otp_verify: Internal server error {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    

@router.post("/resetpassword/")
async def reset_password(
    user: schema.UserNewPassword, db: AsyncSession = Depends(get_db)
):
    try:
        db_user = await UserCrud.get_user_by_email(db, user.email)
        if not db_user:
            print(f"UserRouter -->reset_password: User with email {user.email} is not registered")
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="Email not found"
            )
        
        else:

            db_user.password = user.newPassword
            await db.commit()
            await db.refresh(db_user)
            print(f"UserRouter -->reset_password: User with email {user.email} password is updated")  
            return True              
    except HTTPException as http_exc:
        raise http_exc 

    except Exception as e:
        print(f"UserRouter -->reset_password: Internal server error {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    
