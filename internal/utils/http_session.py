# -*- coding: utf-8 -*-
import asyncio
from contextvars import ContextVar
from typing import Optional

import aiohttp

_AIO_SESSION_MGR: ContextVar[Optional["aiohttp.ClientSession"]] = None


async def setup_session_mgr():
    global _AIO_SESSION_MGR
    _AIO_SESSION_MGR = ContextVar(
        "aiohttp-session", default=aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=32),
            connector_owner=True,
            timeout=aiohttp.ClientTimeout(total=60),
        )
    )  # Acts as a global aiohttp ClientSession that reuses connections.
    await asyncio.sleep(0)
    

async def clear_session_mgr():
    if _AIO_SESSION_MGR is not None:
        session = _AIO_SESSION_MGR.get()
        if session is not None:
            await session.close()
    await asyncio.sleep(0)


def get_aio_session() -> Optional[aiohttp.ClientSession]:
    session = _AIO_SESSION_MGR.get()
    return session
