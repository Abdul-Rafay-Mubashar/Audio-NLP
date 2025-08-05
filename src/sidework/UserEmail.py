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
import hmac, os
import hashlib, random
import mimetypes



class UserEmail:

    def __init__(self,):
        pass

    def encode_id(self, id: int) -> str:
        try:
            id_bytes = str(id).encode("utf-8")
            signature = hmac.new(
                setting.ENCODEING_SECRET_KEY, id_bytes, hashlib.sha256
            ).digest()
            encoded = base64.b32encode(id_bytes + signature[:4]).decode("utf-8")
            return encoded[:25]
        except Exception as e:
            print(f"UserRouter -->encode_id: Error while encodeing id {id}")
            raise HTTPException(
                status_code=500,
                detail="Failed to send activation email"
            )


    def decode_id(self, encoded_id: str) -> int:
        try:
            decoded = base64.b32decode(encoded_id.upper())
            id_bytes, received_signature = decoded[:-4], decoded[-4:]
            expected_signature = hmac.new(
                setting.ENCODEING_SECRET_KEY, id_bytes, hashlib.sha256
            ).digest()[:4]
            if received_signature != expected_signature:
                raise ValueError("Invalid encoded ID: Signature mismatch")
            return int(id_bytes.decode("utf-8"))
        except Exception as e:
            print(f"UserRouter -->decode_id: Error while decodeing encoded id {encoded_id}")
            raise HTTPException(
                status_code=500,
                detail="Failed to send activation email"
            )


    def generate_random_4_digit(self):
        return random.randint(1000, 9999)


    async def send_activation_link_email(self, email: str, id: int, is_admin: bool):
        try:
            message = EmailMessage()
            message["From"] = setting.EMAIL_FROM
            message["To"] = email
            message["Subject"] = "Activate Account"
            link = ""
            if is_admin == True:
                link = f"http://127.0.0.1:8000/api/teacher/activate/{self.encode_id(id)}"
            else:
                link = f"http://127.0.0.1:8000/api/users/activate/{self.encode_id(id)}"
            message.set_content(f"Please Click on link for account activation {link}")

            smtp = SMTP(
                hostname=setting.EMAIL_HOST, port=setting.EMAIL_PORT, use_tls=setting.EMAIL_TLS
            )
            await smtp.connect()
            await smtp.login(setting.EMAIL_FROM, setting.EMAIL_PASSWORD)
            await smtp.send_message(message)
            await smtp.quit()
        except Exception as e:
            print(f"UserRouter -->send_activation_link_email: Error while genrating otp for email {email} due to {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to send activation email"
            )


    async def send_otp_email(self, email: str, otp: int):
        try:
            message = EmailMessage()
            message["From"] = setting.EMAIL_FROM
            message["To"] = email
            message["Subject"] = "Reset Password"
            link = f"Hello There is your OTP for reseting password {otp}"
            message.set_content(f"{link}")

            smtp = SMTP(
                hostname=setting.EMAIL_HOST, port=setting.EMAIL_PORT, use_tls=setting.EMAIL_TLS
            )
            await smtp.connect()
            await smtp.login(setting.EMAIL_FROM, setting.EMAIL_PASSWORD)
            await smtp.send_message(message)
            await smtp.quit()
        except Exception as e:
            print(f"UserRouter -->send_otp_email: Error while genrating otp for email {email}")
            raise HTTPException(
                status_code=500,
                detail="Failed to send activation email"
            )


    async def send_notes_notification(self, course: str, lecture_no: int, email: str, name: str, file_path):
        count = 0
        while True:
            try:
                course_detail = course.split('-')
                print(course_detail)
                message = EmailMessage()
                message["From"] = setting.EMAIL_FROM
                message["To"] = email
                message["Subject"] = "Notes genreated"
                link = f"Hello {name},\n\nYour notes are ready on your request\n\nCourse name: {course_detail[1]}\nSection: {course_detail[2]}\nLecture no: {lecture_no}\n\nThankyou very much for your consideration"

                message.set_content(f"{link}")
                if os.path.exists(file_path):
                    mime_type, _ = mimetypes.guess_type(file_path)
                    mime_type, mime_subtype = mime_type.split('/')
                    with open(file_path, 'rb') as file:
                        file_data = file.read()
                        file_name = os.path.basename(file_path)
                        message.add_attachment(file_data, maintype=mime_type, subtype=mime_subtype, filename=file_name)

                smtp = SMTP(
                    hostname=setting.EMAIL_HOST, port=setting.EMAIL_PORT, use_tls=setting.EMAIL_TLS
                )
                await smtp.connect()
                await smtp.login(setting.EMAIL_FROM, setting.EMAIL_PASSWORD)
                await smtp.send_message(message)
                await smtp.quit()
                print(f"Email sent to {email}")
                break
            except Exception as e:
                print(f"UserRouter -->send_otp_email: Error while genrating otp for email {email} {str(e)}retrying it again {count+1} time")
                count = count + 1
                if count == 3:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to send activation email"
                    )

    async def send_recording_failed_notification(self, course: str, lecture_no: int, email: str, name: str, file_path):
        try:
            course_detail = course.split('-')
            print(course_detail)
            message = EmailMessage()
            message["From"] = setting.EMAIL_FROM
            message["To"] = email
            message["Subject"] = "Recording Failed"
            link = f"Hello {name},\n\nYour request for recording is failed\n\nCourse name: {course_detail[1]}\nSection: {course_detail[2]}\nLecture no: {lecture_no}\n\nWe are sorry about that you are requested to make slides by your own Thankyou"

            message.set_content(f"{link}")

            smtp = SMTP(
                hostname=setting.EMAIL_HOST, port=setting.EMAIL_PORT, use_tls=setting.EMAIL_TLS
            )
            await smtp.connect()
            await smtp.login(setting.EMAIL_FROM, setting.EMAIL_PASSWORD)
            await smtp.send_message(message)
            await smtp.quit()
            print(f"Email sent to {email}")
        except Exception as e:
            print(f"UserRouter -->send_otp_email: Error while genrating otp for email {email} {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to send activation email"
            )
        
    async def send_new_quiz_notification(self, course: str, date: str, time: str, emails: list[str]):
        try:
            course_detail = course.split('-')
            print(course_detail)
            message = EmailMessage()
            message["From"] = setting.EMAIL_FROM
            message["To"] = ", ".join(emails)
            message["Subject"] = "Hello You have a Quiz"
            link = f",\n\nCourse name: {course_detail[1]}\nDate: {date}\nTime: {time}\n\nThankyou"

            message.set_content(f"{link}")

            smtp = SMTP(
                hostname=setting.EMAIL_HOST, port=setting.EMAIL_PORT, use_tls=setting.EMAIL_TLS
            )
            await smtp.connect()
            await smtp.login(setting.EMAIL_FROM, setting.EMAIL_PASSWORD)
            await smtp.send_message(message)
            await smtp.quit()
            print(f"Email sent to {emails}")
        except Exception as e:
            print(f"UserRouter -->send_otp_email: Error while genrating otp for email {emails} {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to send activation email"
            )
        
    async def send_update_quiz_notification(self, course: str, date: str, time: str, emails: list[str]):
        try:
            course_detail = course.split('-')
            print(course_detail)
            message = EmailMessage()
            message["From"] = setting.EMAIL_FROM
            message["To"] = ", ".join(emails)
            message["Subject"] = "Hello Your Quiz Time Is Updated"
            link = f",\n\nCourse name: {course_detail[1]}\nDate: {date}\nTime: {time}\n\nThankyou"

            message.set_content(f"{link}")

            smtp = SMTP(
                hostname=setting.EMAIL_HOST, port=setting.EMAIL_PORT, use_tls=setting.EMAIL_TLS
            )
            await smtp.connect()
            await smtp.login(setting.EMAIL_FROM, setting.EMAIL_PASSWORD)
            await smtp.send_message(message)
            await smtp.quit()
            print(f"Email sent to {emails}")
        except Exception as e:
            print(f"UserRouter -->send_otp_email: Error while genrating otp for email {emails} {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to send activation email"
            )