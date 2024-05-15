# -*- coding: utf-8 -*-
import asyncio
import random

from loguru import logger as loguru_logger


def aretry_with_exponential_backoff(
    *,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 3,
    errors: tuple = (Exception,)
):
    """Retry a function with exponential backoff."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Initialize variables
            num_retries = 0
            delay = initial_delay
            # Loop until a successful response or max_retries is hit or an exception is raised
            while 1:
                try:
                    return await func(*args, **kwargs)
                # Retry on specified errors
                except errors as exc:
                    loguru_logger.error(f"caught error: {exc}, num_retries: {num_retries}.")
                    # Increment retries
                    num_retries += 1
                    # Check if max retries has been reached
                    if num_retries > max_retries:
                        raise Exception(
                            f"Maximum number of retries ({max_retries}) exceeded."
                        )
                    # Increment the delay
                    delay *= exponential_base * (1 + jitter * random.random())
                    # Sleep for the delay
                    loguru_logger.info(f"create (backoff): sleeping for {delay} seconds.")
                    await asyncio.sleep(delay)
                # Raise exceptions for any errors not specified
                except Exception as exc:
                    raise exc
        return wrapper
    return decorator


def aretry_with_constant_backoff(
    *,
    constant_delay: float = 1,
    jitter: bool = True,
    max_retries: int = 3,
    errors: tuple = (Exception,)
):
    """Retry a function with constant backoff."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Initialize variables
            num_retries = 0
            # Loop until a successful response or max_retries is hit or an exception is raised
            while 1:
                try:
                    return await func(*args, **kwargs)
                # Retry on specified errors
                except errors as exc:
                    loguru_logger.error(f"caught error: {exc}, num_retries: {num_retries}.")
                    # Increment retries
                    num_retries += 1
                    # Check if max retries has been reached
                    if num_retries > max_retries:
                        raise Exception(
                            f"Maximum number of retries ({max_retries}) exceeded."
                        )
                    # Compute the delay
                    delay = constant_delay * (1 + jitter * random.random())
                    # Sleep for the delay
                    loguru_logger.info(f"create (backoff): sleeping for {delay} seconds.")
                    await asyncio.sleep(delay)
                # Raise exceptions for any errors not specified
                except Exception as exc:
                    raise exc
        return wrapper
    return decorator
