# -*- coding: utf-8 -*-
import asyncio
import platform
import random
import sys
import time
from functools import wraps

from loguru import logger as loguru_logger

from internal.constants import PUNCTUATION_LIST


def timeit(func):
    """Decorator that logs the time a function takes to execute."""

    async def process(func, *args, **kwargs):
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return await async_wrapper(func(*args, **kwargs))

    @wraps(func)
    async def wrapper(*args, **kwargs):
        st = time.time()
        result = await process(func, *args, **kwargs)
        ed = time.time()
        loguru_logger.debug(f"{func.__name__} took time: {ed - st:.3f} secs.")
        return result

    return wrapper


def async_wrapper(func):
    """Decorator that wraps a synchronous function in an asynchronous wrapper."""
    async def inner(*args, **kwargs):
        await asyncio.sleep(0)
        return func(*args, **kwargs)
    return inner


ALL_DIGIT_NUMS_AND_LETTERS = [str(i) for i in range(0, 10)] + \
    [str(chr(i)) for i in range(ord('a'), ord('z') + 1)] + \
    [str(chr(i)) for i in range(ord('A'), ord('Z') + 1)]
ALL_DIGIT_NUMS_AND_LETTERS_TOTAL = len(ALL_DIGIT_NUMS_AND_LETTERS)


def gen_n_digit_nums_and_letters(n: int) -> str:
    """Generate a random string of n digits and letters."""
    seed = random.randrange(sys.maxsize)
    random.seed(seed)
    for i in range(len(ALL_DIGIT_NUMS_AND_LETTERS) - 1, 0, -1):
        j = random.randrange(i + 1)
        ALL_DIGIT_NUMS_AND_LETTERS[i], ALL_DIGIT_NUMS_AND_LETTERS[j] = ALL_DIGIT_NUMS_AND_LETTERS[j], ALL_DIGIT_NUMS_AND_LETTERS[i]
    nums_and_letters = [ALL_DIGIT_NUMS_AND_LETTERS[random.randrange(ALL_DIGIT_NUMS_AND_LETTERS_TOTAL)] for _ in range(n)]
    return "".join(nums_and_letters)


def convert_ts(ts: int) -> str:
    """Convert a timestamp to a formatted string."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def get_system_info() -> str:
    """Get the system information."""
    return f"Python:{platform.python_version()}, Platform:{platform.platform()}, System:{platform.system()}"


def get_hostname() -> str:
    """Get the hostname."""
    return platform.node()


def is_text_all_punctuation(text: str) -> bool:
    """Check if a text is all punctuation."""
    yes = True
    for char in text:
        if str(char) not in PUNCTUATION_LIST:
            yes = False
            break
    return yes


def remove_all_punctuations(text: str) -> str:
    """Remove all punctuations from a text."""
    new_text_arr = []
    for char in text:
        if str(char) not in PUNCTUATION_LIST:
            new_text_arr.append(str(char))
    return "".join(new_text_arr)
