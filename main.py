from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import setting, asyncio
from src.db.models import models
from src.router import UserRouters, QuizRouters, TeacherRouter, RecorderRouter, NoteRouters, TeacherCourseRouter
from fastapi.middleware.cors import CORSMiddleware
from src.sidework import check_audio_queue, check_notes_queue, check_notes_status_in_db, run_quiz_processor
from fastapi.staticfiles import StaticFiles



engine = create_async_engine(setting.DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


Base = models.Base
app = FastAPI()

app.mount("/notes", StaticFiles(directory=r"C:\Users\Hp\Desktop\FYP\notes"), name="notes")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)


app.include_router(UserRouters.router, prefix="/api")
app.include_router(QuizRouters.router, prefix="/api")
app.include_router(TeacherRouter.router, prefix="/api")
app.include_router(RecorderRouter.router, prefix="/api")
app.include_router(NoteRouters.router, prefix="/api")
app.include_router(TeacherCourseRouter.router, prefix="/api")






@app.on_event("startup")
async def on_startup():
    asyncio.create_task(check_audio_queue())
    asyncio.create_task(check_notes_queue())
    asyncio.create_task(check_notes_status_in_db())
    asyncio.create_task(run_quiz_processor())

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created!")

