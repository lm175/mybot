import aiosqlite
from aiosqlite import Row

from pathlib import Path
import asyncio


# 数据存放目录
dir_path = Path("data/ninja3/")
if not dir_path.exists():
    dir_path.mkdir(parents=True, exist_ok=True)

db_path = dir_path / "giftcodes.db"
if not db_path.exists():
    db_path.touch()


async def create_table():
    async with aiosqlite.connect(db_path) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS gameids (
                game_id INTEGER PRIMARY KEY,
                user_id INTEGER
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS giftcodes (
                code TEXT PRIMARY KEY,
                time DATE,
                available INTEGER DEFAULT 1
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                need_remind INTEGER DEFAULT 1
            )
        ''')
        await db.commit()

asyncio.run(create_table())


class DatabaseManager:

    @staticmethod
    async def execute(query: str, params: tuple) -> None:
        async with aiosqlite.connect(db_path) as db:
            await db.execute(query, params)
            await db.commit()

    @staticmethod
    async def query_one(query: str, params: tuple) -> Row | None:
        async with aiosqlite.connect(db_path) as db:
            async with db.execute(query, params) as cursor:
                return await cursor.fetchone()

    @staticmethod
    async def query_all(query: str, params: tuple) -> list[Row]:
        async with aiosqlite.connect(db_path) as db:
            async with db.execute(query, params) as cursor:
                result = []
                rows = await cursor.fetchall()
                for row in rows:
                    result.append(row)
                return result
    
    @staticmethod
    async def get_all_uids() -> dict[int, int]:
        result = {}
        async with aiosqlite.connect(db_path) as db:
            async with db.execute(
                "SELECT * FROM gameids"
            ) as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    result[row[0]] = row[1]
        return result

    @staticmethod
    async def get_user_uids(user_id: int) -> list[int]:
        result = []
        async with aiosqlite.connect(db_path) as db:
            async with db.execute(
                "SELECT game_id FROM gameids WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    result.append(row[0])
        return result