import pytest
from sqlalchemy import text

from tests.conftest import test_engine


@pytest.mark.asyncio
async def test_database_connection():

    async with test_engine.connect() as conn:

        result = await conn.execute(
            text("SELECT 1")
        )

        value = result.scalar()

        assert value == 1