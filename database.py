# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base, Session

# DB_URL = "mysql+pymysql://root:Atul%402006@localhost/e_comm"

# engine = create_engine(DB_URL)
# SessionLocal = sessionmaker(bind=engine)

# Base = declarative_base()


"""async non-blocking """

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings
import os


DATABASE_URL = (
    settings.TEST_DB_URL
    if os.getenv("TESTING")
    else settings.DB_URL
)

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    connect_args={
        "ssl": {
            "ssl": True
        }
    })
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# ============================
# Database Dependency
# ============================

async def get_db():

    async with AsyncSessionLocal() as db:

        yield db