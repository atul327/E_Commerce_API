"""
=========================================================
Purpose:
--------
Common pytest configuration.

Responsibilities:
1. Create Test Database Engine
2. Create Tables Before Tests
3. Drop Tables After Tests
4. Override FastAPI get_db()
5. Provide Async Test Client
=========================================================
"""

import os

os.environ["TESTING"] = "1"


import pytest

from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession
)

from sqlalchemy.orm import sessionmaker

from config import settings
from database import Base, get_db
from main import app



# =========================================================
# TEST DATABASE URL
# =========================================================

TEST_DATABASE_URL = settings.TEST_DB_URL



# =========================================================
# GLOBAL VARIABLE
# Stores current test engine
# =========================================================

current_test_engine = None



# =========================================================
# TEST ENGINE FIXTURE
# =========================================================

@pytest.fixture(scope="function")
async def test_engine():

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=True
    )

    yield engine


    # Close all connections
    await engine.dispose()



# =========================================================
# CREATE / DROP TABLES
# =========================================================

@pytest.fixture(scope="function", autouse=True)
async def prepare_database(test_engine):

    global current_test_engine

    current_test_engine = test_engine


    print("\nCreating Test Database Tables...\n")


    async with test_engine.begin() as conn:

        await conn.run_sync(
            Base.metadata.create_all
        )


    yield


    print("\nDeleting Test Database Tables...\n")


    async with test_engine.begin() as conn:

        await conn.run_sync(
            Base.metadata.drop_all
        )



# =========================================================
# TEST DATABASE SESSION
# =========================================================

@pytest.fixture
async def db_session(test_engine):

    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


    async with TestingSessionLocal() as session:

        yield session



# =========================================================
# OVERRIDE FastAPI get_db()
# =========================================================

async def override_get_db():

    TestingSessionLocal = sessionmaker(
        bind=current_test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


    async with TestingSessionLocal() as db:

        yield db



# Replace production database dependency

app.dependency_overrides[get_db] = override_get_db



# =========================================================
# ASYNC TEST CLIENT
# =========================================================

@pytest.fixture
async def client():

    transport = ASGITransport(
        app=app
    )


    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:

        yield client