from pydantic import BaseModel  # Import Pydantic for schema validation
import setting
from datetime import timedelta
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base


engine = create_async_engine(setting.DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Settings(BaseModel):
    authjwt_secret_key: str = setting.AUTHJWT_SECRET_KEY
    authjwt_access_token_expires: timedelta = timedelta(hours=24)

@AuthJWT.load_config
def get_config():
    return Settings()

async def get_db():
    async with async_session() as session:
        yield session