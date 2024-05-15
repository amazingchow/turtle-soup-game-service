# -*- coding: utf-8 -*-
import asyncio
import random
from typing import Any, Dict, List, Optional, Tuple

import aiomysql
import jsonschema
import pymysql.err as perrors
from loguru import logger as loguru_logger

from internal.classes.singleton import Singleton
from internal.utils.helper import timeit
from internal.utils.retry_with_backoff import aretry_with_constant_backoff


class MySQLClientSetupException(Exception):
    pass


class MySQLException(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors


class MySQLClient(metaclass=Singleton):
    """
    MySQL custom client.
    """

    DB_CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "host": {"type": "string"},
            "port": {"type": "integer"},
            "username": {"type": "string"},
            "password": {"type": "string"}
        },
        "required": [
            "host",
            "port",
            "username",
            "password"
        ]
    }
    DB_CONFIG_HOST: str
    DB_CONFIG_PORT: int
    DB_CONFIG_USR: str
    DB_CONFIG_PWD: str

    def __init__(
        self,
        *,
        client_conf: Dict[str, Any],
        io_loop: Optional[asyncio.BaseEventLoop] = None
    ):
        if not self._validate_config(client_conf):
            raise MySQLClientSetupException("Please check your MySQLClient configuration.")
        if not io_loop:
            raise MySQLClientSetupException("Please provide an event loop to MySQLClient.")
        
        self.DB_CONFIG_HOST = client_conf["host"]
        self.DB_CONFIG_PORT = client_conf["port"]
        self.DB_CONFIG_USR = client_conf["username"]
        self.DB_CONFIG_PWD = client_conf["password"]
        self._loop = io_loop or asyncio.get_event_loop()

    def _validate_config(self, conf: Dict[str, Any]) -> bool:
        valid = False
        try:
            jsonschema.validate(instance=conf, schema=self.DB_CONFIG_SCHEMA)
            valid = True
        except jsonschema.ValidationError:
            loguru_logger.error(f"Invalid MySQLClient configuration, conf:{conf}.")
        finally:
            return valid

    async def connect(self) -> None:
        self._pool: aiomysql.Pool = await aiomysql.create_pool(
            host=self.DB_CONFIG_HOST,
            port=self.DB_CONFIG_PORT,
            user=self.DB_CONFIG_USR,
            password=self.DB_CONFIG_PWD,
            minsize=5,
            maxsize=10,
            autocommit=True,
            pool_recycle=3600,
            loop=self._loop
        )

    async def is_connected(self) -> bool:
        connected = False
        try:
            conn: Optional[aiomysql.Connection] = None
            async with self._pool.acquire() as conn:
                await conn.ping(reconnect=True)
            connected = True
        except perrors.MySQLError as exc:
            loguru_logger.error(f"Failed to ping MySQL server, err:{exc}.")
        finally:
            return connected

    @timeit
    @aretry_with_constant_backoff(constant_delay=1, jitter=True, max_retries=3, errors=(MySQLException,))
    async def execute_r(self, sql: str) -> Tuple[List[List[Any]], bool]:
        done = False
        rets: List[List[Any]] = []
        try:
            conn: Optional[aiomysql.Connection] = None
            async with self._pool.acquire() as conn:
                cur: Optional[aiomysql.DictCursor] = None
                async with conn.cursor() as cur:
                    await cur.execute(sql)
                    loguru_logger.debug(f"Executed stmt:{sql}.")
                    rets = await cur.fetchall()
            done = True
        except perrors.OperationalError as exc:
            loguru_logger.error(f"Failed to execute stmt:{sql}, err:{exc}.")
            raise MySQLException(f"Failed to execute stmt:{sql}, err:{exc}.")
        return (rets, done)

    @timeit
    async def execute_w(self, sql: str, values: List[Tuple] = [], for_update: bool = False) -> bool:
        done = False
        try:
            conn: Optional[aiomysql.Connection] = None
            async with self._pool.acquire() as conn:
                cur: Optional[aiomysql.DictCursor] = None
                try:
                    async with conn.cursor() as cur:
                        if for_update:
                            await cur.execute(sql)
                            loguru_logger.debug(f"Executed stmt:{sql}.")
                        else:
                            await cur.executemany(sql, values)
                            loguru_logger.debug(f"Executed stmt:{sql}.")
                    await conn.commit()
                except perrors.IntegrityError as exc:
                    # NOTE: 重复插入数据时, 忽略错误
                    loguru_logger.warning(f"Failed to execute stmt:{sql}, err:{exc}.")
                    await conn.rollback()
            done = True
        except Exception as exc:
            loguru_logger.error(f"Failed to execute stmt:{sql}, err:{exc}.")
        finally:
            return done

    @staticmethod
    async def random_sleep(min: int, max: int):
        await asyncio.sleep(random.randint(min, max) / 1000)

    async def close(self):
        self._pool.close()
        await self._pool.wait_closed()


_instance: Optional[MySQLClient] = None


def init_instance(client_conf: Dict[str, Any], io_loop: Optional[asyncio.BaseEventLoop] = None):
    global _instance
    _instance = MySQLClient(client_conf=client_conf, io_loop=io_loop)


def instance() -> MySQLClient:
    return _instance
