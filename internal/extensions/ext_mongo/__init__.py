# -*- coding: utf-8 -*-
import asyncio
import random
from typing import Any, Dict, Optional

import jsonschema
import pymongo
import pymongo.collection as pc
import pymongo.database as pd
import pymongo.errors as perrors
import pymongo.mongo_client as pmc
from loguru import logger as loguru_logger
from motor.motor_asyncio import AsyncIOMotorClient

from internal.classes.singleton import Singleton
from internal.utils.helper import timeit
from internal.utils.retry_with_backoff import aretry_with_constant_backoff


class MongoDBClientSetupException(Exception):
    pass


class MongoDBClient(metaclass=Singleton):
    """
    MongoDB custom client.
    """

    DB_CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "endpoint": {"type": "string"},
            "username": {"type": "string"},
            "password": {"type": "string"},
            "auth_mechanism": {"type": "string"},
            "database": {"type": "string"},
            "collection": {"type": "string"}
        },
        "required": [
            "endpoint",
            "username",
            "password",
            "auth_mechanism",
            "database",
            "collection"
        ],
    }

    def __init__(
        self,
        *,
        client_conf: Dict[str, Any],
        io_loop: Optional[asyncio.BaseEventLoop] = None
    ):
        if not self._validate_config(client_conf):
            raise MongoDBClientSetupException("Please check your MongoDBClient configuration.")
        if not io_loop:
            raise MongoDBClientSetupException("Please provide an event loop to MongoDBClient.")

        self._client: pmc.MongoClient = AsyncIOMotorClient(
            "mongodb://{}/".format(client_conf["endpoint"]),
            username=client_conf["username"],
            password=client_conf["password"],
            authSource="admin",
            authMechanism=client_conf["auth_mechanism"],
            serverSelectionTimeoutMS=2000,
            socketTimeoutMS=5000,
            connectTimeoutMS=2000,
            io_loop=io_loop,
        )
        self._conf = client_conf

    def _validate_config(self, conf: Dict[str, Any]) -> bool:
        valid = False
        try:
            jsonschema.validate(instance=conf, schema=self.DB_CONFIG_SCHEMA)
            valid = True
        except jsonschema.ValidationError:
            loguru_logger.error(f"Invalid MongoDBClient configuration, conf:{conf}.")
        finally:
            return valid

    async def is_connected(self) -> bool:
        connected = False
        try:
            self._db: pd.Database = self._client[self._conf["database"]]
            res = await self._db.command("ping")
            connected = res["ok"] == 1.0
            if connected:
                loguru_logger.debug(f"MongoDB Cluster Nodes ==> {self._client.nodes}")
                try:
                    self._store: pc.Collection = self._db[self._conf["collection"]]
                    for index in self._conf["indexes"]:
                        if index["direction"] == 1:
                            await self._store.create_index(
                                index["name"], pymongo.ASCENDING, unique=index["unique"], background=True, sparse=False
                            )
                        elif index["direction"] == -1:
                            await self._store.create_index(
                                index["name"], pymongo.DESCENDING, unique=index["unique"], background=True, sparse=False
                            )
                except perrors.DuplicateKeyError:
                    pass
                except Exception as exc:
                    loguru_logger.error(f"Failed to create indexes, err:{exc}.")
        except perrors.ServerSelectionTimeoutError as exc:
            loguru_logger.error(f"Failed to ping MongoDB server, err:{exc}.")
        finally:
            return connected

    @timeit
    @aretry_with_constant_backoff(constant_delay=1, jitter=True, max_retries=3, errors=(perrors.NetworkTimeout, perrors.ExecutionTimeout,))
    async def do_sth(self) -> bool:
        done = False
        try:
            done = True
        except perrors.PyMongoError as exc:
            if exc.timeout:
                pass
            else:
                pass
            raise exc
        except Exception:
            pass
        finally:
            return done

    @staticmethod
    async def random_sleep(min: int, max: int):
        await asyncio.sleep(random.randint(min, max) / 1000)

    async def close(self):
        self._client.close()
        await asyncio.sleep(0)


_instance: Optional[MongoDBClient] = None


def init_instance(client_conf: Dict[str, Any], io_loop: Optional[asyncio.BaseEventLoop] = None):
    global _instance
    _instance = MongoDBClient(client_conf=client_conf, io_loop=io_loop)


def instance() -> MongoDBClient:
    return _instance
