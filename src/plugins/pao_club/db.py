import aiosqlite

from pathlib import Path
from typing import Dict
import asyncio


dir_path = Path("data/pao_club/")
if not dir_path.exists():
    dir_path.mkdir(parents=True, exist_ok=True)

data_path = dir_path / "club.db"
if not data_path.exists():
    data_path.touch()


async def create_table():
    async with aiosqlite.connect(data_path) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                question TEXT PRIMARY KEY,
                answer TEXT,
                submitter INTEGER
            )
        ''')
        await db.commit()

asyncio.run(create_table())



class DatabaseManager:

    @staticmethod
    async def query(keyword: str) -> str:
        """通过题目关键词查询"""
        async with aiosqlite.connect(data_path) as db:
            keyword = keyword.replace('%', r'\%').replace('_', r'\_')
            async with db.execute('''
                select question, answer from questions
                        where question like ? escape '\\'
            ''', (f"%{keyword}%",)) as cursor:
                rows = await cursor.fetchall()
                result = ""
                if rows:
                    for row in rows:
                        result += f"题目: {row[0]}\n"
                        result += f"答案: {row[1]}\n\n"
                else:
                    result += f"未找到与关键词 '{keyword}' 相关的记录"

                return result.strip()
    
    @staticmethod
    async def update(data: Dict[str, str], user_id: int) -> int:
        """更新数据库内容，返回新增题目的数量"""
        async with aiosqlite.connect(data_path) as db:
            async with db.execute('''
                SELECT COUNT(*) FROM questions WHERE submitter = ?
            ''', (user_id,)) as cursor:
                old_count = (await cursor.fetchone())[0] # type: ignore

            for k, v in data.items():
                if k is None or v is None:
                    continue  # 跳过无效条目
                await db.execute('''
                    INSERT OR IGNORE INTO questions
                        (question, answer, submitter)
                        VALUES (?, ?, ?)
                ''', (k, v, user_id))
            await db.commit()

            async with db.execute('''
                SELECT COUNT(*) FROM questions WHERE submitter = ?
            ''', (user_id,)) as cursor:
                new_count = (await cursor.fetchone())[0] # type: ignore
            
            return new_count - old_count
    
    @staticmethod
    async def get_count(user_id: int = 0) -> int:
        """查询user_id的题目数量，不传入user_id则查询总数"""
        async with aiosqlite.connect(data_path) as db:
            if user_id:
                async with db.execute('''
                    SELECT COUNT(*) FROM questions WHERE submitter = ?
                ''', (user_id,)) as cursor:
                    return (await cursor.fetchone())[0] # type: ignore
            else:
                async with db.execute('''
                    SELECT COUNT(*) FROM questions
                ''') as cursor:
                    return (await cursor.fetchone())[0] # type: ignore
        