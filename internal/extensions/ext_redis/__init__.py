# -*- coding: utf-8 -*-
import asyncio
import platform
import random
import socket
from typing import Any, Dict, List, Optional, Tuple

import jsonschema
import redis.asyncio as aio_redis
import redis.exceptions as redis_exceptions
from loguru import logger as loguru_logger

from internal.classes.singleton import Singleton
from internal.utils.helper import timeit
from internal.utils.retry_with_backoff import aretry_with_constant_backoff


class RedisClientSetupException(Exception):
    pass


class RedisClient(metaclass=Singleton):
    """
    Redis custom client.
    """

    DB_CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "endpoint": {"type": "string"},
            "password": {"type": "string"},
            "db": {"type": "number"},
            "socket_timeout": {"type": "number"}
        },
        "required": [
            "endpoint",
            "password",
            "db"
        ]
    }

    def __init__(
        self,
        *,
        client_conf: Dict[str, Any],
        io_loop: Optional[asyncio.BaseEventLoop] = None
    ):
        if not self._validate_config(client_conf):
            raise RedisClientSetupException("Please check your RedisClient configuration.")

        host, port = client_conf["endpoint"].split(":")[0], int(client_conf["endpoint"].split(":")[1])
        if platform.system() == "Linux":
            socket_keepalive_options = {
                # 600秒内没有数据传输时开始发送TCP KEEPALIVE探测包
                socket.TCP_KEEPIDLE: 600,
                # 发送TCP KEEPALIVE探测包的次数
                socket.TCP_KEEPCNT: 3,
                # 两次探测包之间的时间间隔
                socket.TCP_KEEPINTVL: 10
            }
        else:
            socket_keepalive_options = {}
        _pool = aio_redis.BlockingConnectionPool(
            # NOTE: 设置最大连接数, 防止连接过多导致redis服务端资源耗尽
            max_connections=100,
            timeout=5,
            host=host,
            port=port,
            db=client_conf["db"],
            password=client_conf["password"],
            socket_timeout=client_conf.get("socket_timeout", 5),
            socket_connect_timeout=2,
            # NOTE: 设置TCP KEEPALIVE参数, 确保在连接空闲时, 客户端和服务器之间的TCP连接保持活动状态
            socket_keepalive=True,
            socket_keepalive_options=socket_keepalive_options
        )
        self._client = aio_redis.Redis.from_pool(connection_pool=_pool)

    def _validate_config(self, conf: Dict[str, Any]) -> bool:
        valid = False
        try:
            jsonschema.validate(instance=conf, schema=self.DB_CONFIG_SCHEMA)
            valid = True
        except jsonschema.ValidationError:
            loguru_logger.error(f"Invalid RedisClient configuration, conf:{conf}.")
        finally:
            return valid

    async def is_connected(self) -> bool:
        connected = False
        try:
            connected = await self._client.ping()
        except redis_exceptions.RedisError as exc:
            loguru_logger.error(f"Failed to ping Redis server, err:{exc}.")
        finally:
            return connected

    def get_connection(self) -> aio_redis.Redis:
        return self._client

    @timeit
    @aretry_with_constant_backoff(constant_delay=1, jitter=True, max_retries=3, errors=(redis_exceptions.TimeoutError,))
    async def batch_get_string(self, keys: List[str]) -> Tuple[List[Optional[str]], bool]:
        done = False
        result = []
        try:
            pipe = self._client.pipeline()
            for key in keys:
                pipe.get(key)
            result = await pipe.execute()
            for idx, value in enumerate(result):
                if value is not None and isinstance(value, bytes):
                    result[idx] = value.decode("utf-8")
            done = True
        except redis_exceptions.TimeoutError:
            loguru_logger.error(f"Timeout to batch get value for keys:{keys}.")
            raise redis_exceptions.TimeoutError
        except Exception as e:
            loguru_logger.error(f"Failed to batch get value for keys:{keys}, err:{e}.")
        finally:
            return (result, done)

    @timeit
    @aretry_with_constant_backoff(constant_delay=1, jitter=True, max_retries=3, errors=(redis_exceptions.TimeoutError,))
    async def cache_string(self, key: str, value: str, ttl: int = 0) -> bool:
        done = False
        try:
            if ttl > 0:
                await self._client.execute_command("SET", key, value, "EX", ttl)
            else:
                await self._client.execute_command("SET", key, value)
            done = True
        except redis_exceptions.TimeoutError:
            loguru_logger.error(f"Timeout to set value for key:{key}.")
            raise redis_exceptions.TimeoutError
        except Exception as e:
            loguru_logger.error(f"Failed to set value for key:{key}, err:{e}.")
        finally:
            return done

    @timeit
    @aretry_with_constant_backoff(constant_delay=1, jitter=True, max_retries=3, errors=(redis_exceptions.TimeoutError,))
    async def exist_or_get_string(self, key: str) -> Tuple[Optional[str], bool, bool]:
        value = None
        existed = False
        done = False
        try:
            value = await self._client.execute_command("GET", key)
            if value is not None and isinstance(value, bytes):
                value = value.decode("utf-8")
                existed = True
            done = True
        except redis_exceptions.TimeoutError:
            loguru_logger.error(f"Timeout to get value for key:{key}.")
            raise redis_exceptions.TimeoutError
        except Exception as e:
            loguru_logger.error(f"Failed to get value for key:{key}, err:{e}.")
        finally:
            return (value, existed, done)

    @timeit
    @aretry_with_constant_backoff(constant_delay=1, jitter=True, max_retries=3, errors=(redis_exceptions.TimeoutError,))
    async def cache_integer(self, key: str, value: int, ttl: int = 0) -> bool:
        done = False
        try:
            if ttl > 0:
                await self._client.execute_command("SET", key, value, "EX", ttl)
            else:
                await self._client.execute_command("SET", key, value)
            done = True
        except redis_exceptions.TimeoutError:
            loguru_logger.error(f"Timeout to set value for key:{key}.")
            raise redis_exceptions.TimeoutError
        except Exception as e:
            loguru_logger.error(f"Failed to set value for key:{key}, err:{e}.")
        finally:
            return done

    @timeit
    @aretry_with_constant_backoff(constant_delay=1, jitter=True, max_retries=3, errors=(redis_exceptions.TimeoutError,))
    async def incr_integer(self, key: str) -> bool:
        done = False
        try:
            await self._client.execute_command("INCR", key)
            done = True
        except redis_exceptions.TimeoutError:
            loguru_logger.error(f"Timeout to incr for key:{key}.")
            raise redis_exceptions.TimeoutError
        except Exception as e:
            loguru_logger.error(f"Failed to incr for key:{key}, err:{e}.")
        finally:
            return done

    @timeit
    @aretry_with_constant_backoff(constant_delay=1, jitter=True, max_retries=3, errors=(redis_exceptions.TimeoutError,))
    async def decr_integer(self, key: str) -> bool:
        done = False
        try:
            await self._client.execute_command("DECR", key)
            done = True
        except redis_exceptions.TimeoutError:
            loguru_logger.error(f"Timeout to decr for key:{key}.")
            raise redis_exceptions.TimeoutError
        except Exception as e:
            loguru_logger.error(f"Failed to decr for key:{key}, err:{e}.")
        finally:
            return done

    @timeit
    @aretry_with_constant_backoff(constant_delay=1, jitter=True, max_retries=3, errors=(redis_exceptions.TimeoutError,))
    async def exist_or_get_integer(self, key: str) -> Tuple[Optional[int], bool, bool]:
        value = None
        existed = False
        done = False
        try:
            value = await self._client.execute_command("GET", key)
            if value is not None and isinstance(value, bytes):
                value = int(value.decode("utf-8"))
                existed = True
            done = True
        except redis_exceptions.TimeoutError:
            loguru_logger.error(f"Timeout to get value for key:{key}.")
            raise redis_exceptions.TimeoutError
        except Exception as e:
            loguru_logger.error(f"Failed to get value for key:{key}, err:{e}.")
        finally:
            return (value, existed, done)

    @staticmethod
    async def random_sleep(min: int, max: int):
        await asyncio.sleep(random.randint(min, max) / 1000)

    async def close(self):
        await self._client.aclose()


_instance: Optional[RedisClient] = None


def init_instance(client_conf: Dict[str, Any], io_loop: Optional[asyncio.BaseEventLoop] = None):
    global _instance
    _instance = RedisClient(client_conf=client_conf, io_loop=io_loop)


def instance() -> RedisClient:
    return _instance
