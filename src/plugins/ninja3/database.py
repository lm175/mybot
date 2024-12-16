from pathlib import Path
from datetime import date, datetime
from typing import Union
from collections.abc import Iterable

import aiosqlite
from nonebot import get_driver
from aiosqlite import Row

from .requires import store
from .utils import is_this_week

class AsyncDatabase:
    def __init__(self, db_name: Union[str, Path]):
        self.db_name = db_name

    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_name)

    async def execute(self, sql: str, params: Union[tuple, list, dict]=()):
        return await self.conn.execute(sql, params)
    
    async def commit(self):
        await self.conn.commit()

    async def close(self):
        await self.conn.close()



    async def get_available_codes(self) -> list[str]:
        """获取可用兑换码列表"""
        result = await (await self.execute(
            "SELECT code FROM giftcodes WHERE available=1"
        )).fetchall()
        return [r[0] for r in result]


    async def code_exists(self, code: str) -> bool:
        """检查兑换码是否已存在"""
        cursor = await self.execute(
            "SELECT code FROM giftcodes WHERE code=? LIMIT 1",
            (code,)
        )
        return bool(await cursor.fetchone())
    

    async def code_add(self, code: str, time: date, available: bool) -> None:
        """添加兑换码信息"""
        await self.execute(
            "INSERT INTO giftcodes (code, time, available) VALUES (?, ?, ?)",
            (code, time, available)
        )
        await self.commit()
    

    async def codes_update(self) -> None:
        """更新兑换码可用状态"""
        codes = await (await self.execute(
            "SELECT * FROM giftcodes WHERE available=1"
        )).fetchall()
        updates: list[str] = []
        for c in codes:
            if not is_this_week(datetime.strptime(c[1], "%Y-%m-%d").date()):
                updates.append(c[0])
        if updates:
            placeholders = ', '.join(['?'] * len(updates))
            sql = f"UPDATE giftcodes SET available=0 WHERE code IN ({placeholders})"
            await self.execute(sql, updates)
            await self.commit()


    async def get_users(self) -> Iterable[Row]:
        """获取所有用户"""
        return await (await self.execute(
            "SELECT * FROM users"
        )).fetchall()
    

    async def get_user_info(self, user_id: int) -> Union[Row, None]:
        """查询用户的信息"""
        return await (await self.execute(
            "SELECT * FROM users WHERE user_id=?",
            (user_id,)
        )).fetchone()
    

    async def user_add(self, user_id: int, uid_nums: int, need_remind: bool) -> None:
        """添加用户信息"""
        await self.execute(
            "INSERT INTO users (user_id, uid_nums, need_remind) VALUES (?, ?, ?)",
            (user_id, uid_nums, need_remind)
        )
        await self.commit()
    

    async def user_update(self, user_id: int) -> None:
        """更新用户信息"""
        uids = await self.get_user_uids(user_id)
        if not uids:
            await self.execute(
                "DELETE FROM users WHERE user_id=?",
                (user_id,)
            )
        else:
            await self.execute(
                "UPDATE users SET uid_nums=? WHERE user_id=?",
                (len(uids), user_id)
            )
        await self.commit()
    

    async def user_remind(self, user_id: int, need_remind: bool) -> None:
        """更改提醒状态"""
        await self.execute(
            "UPDATE users SET need_remind=? WHERE user_id=?",
            (need_remind, user_id)
        )
        await self.commit()


    async def get_user_uids(self, user_id: int) -> list[int]:
        """获取用户的所有uid"""
        rows = await (await self.execute(
            "SELECT game_id FROM gameids WHERE user_id=?",
            (user_id,)
        )).fetchall()
        return [r[0] for r in rows]
    

    async def get_gameid_info(self, game_id: int) -> Union[Row, None]:
        """查询uid信息"""
        return await (await self.execute(
            "SELECT * FROM gameids WHERE game_id=?",
            (game_id,)
        )).fetchone()
    

    async def gameid_add(self, game_id: int, user_id: int) -> None:
        """添加uid"""
        await self.execute(
            "INSERT INTO gameids (game_id, user_id) VALUES (?, ?)",
            (game_id, user_id)
        )
        await self.commit()
    

    async def gameid_del(self, game_id: int) -> None:
        """删除uid"""
        await self.execute(
            "DELETE FROM gameids WHERE game_id=?",
            (game_id,)
        )
        await self.commit()
    




db_instance = AsyncDatabase(db_name=store.get_plugin_data_file('giftcodes.db'))


driver = get_driver()

@driver.on_startup
async def start():
    try:
        await db_instance.connect()
        await db_instance.execute('''
            CREATE TABLE IF NOT EXISTS gameids (
                game_id INTEGER PRIMARY KEY,
                user_id INTEGER
            ) WITHOUT ROWID;
        ''')
        await db_instance.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                uid_nums INTEGER,
                need_remind INTEGER DEFAULT 1
            ) WITHOUT ROWID;
        ''')
        await db_instance.execute('''
            CREATE TABLE IF NOT EXISTS giftcodes (
                code TEXT PRIMARY KEY,
                time DATE,
                available INTEGER DEFAULT 1
            );
        ''')
        print("Database schema connected.")
    except Exception as e:
        print(f"Failed to connect database: {e}")


@driver.on_shutdown
async def close():
    await db_instance.close()