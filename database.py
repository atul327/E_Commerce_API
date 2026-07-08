# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base, Session

# DB_URL = "mysql+pymysql://root:Atul%402006@localhost/e_comm"

# engine = create_engine(DB_URL)
# SessionLocal = sessionmaker(bind=engine)

# Base = declarative_base()


"""async non-blocking """

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base

DB_URL = "mysql+asyncmy://root:Atul%402006@localhost/e_comm"

engine = create_async_engine(DB_URL)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()