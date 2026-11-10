import pytest
from sqlalchemy import inspect


@pytest.mark.asyncio
async def test_sqlite_database_creates_tables(test_db):
    connection = await test_db.connection()

    table_names = await connection.run_sync(
        lambda sync_connection: inspect(
            sync_connection
        ).get_table_names()
    )

    assert "users" in table_names
    assert "vendors" in table_names
    assert "categories" in table_names
    assert "products" in table_names