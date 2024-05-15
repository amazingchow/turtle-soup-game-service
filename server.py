# -*- coding: utf-8 -*-
import os
import sys

sys.path.append(os.path.join(os.path.abspath(os.curdir), "internal", "proto_gens"))

import argparse
import asyncio
import random
import time
import traceback
from typing import Any, Dict

import grpc
from grpc_reflection.v1alpha import reflection
from loguru import logger as loguru_logger

from internal.logger.loguru_logger import init_global_logger
from internal.proto_gens import (
    turtle_soup_game_service_pb2,
    turtle_soup_game_service_pb2_grpc
)
from internal.service.impl import TurtleSoupGameService
from internal.utils.global_vars import get_config, set_config

# Coroutine to be invoked when the event loop is shutting down.
_cleanup_coroutines = []


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--conf",
        type=str,
        default="./etc/turtle-soup-game-service-dev.json",
        help="the service config file",
    )
    args = parser.parse_args()
    set_config(args.conf)


async def serve(conf: Dict[str, Any]):
    global _cleanup_coroutines

    try:
        # Create an asyncio gRPC server.
        server = grpc.aio.server(
            options=(
                ("grpc.keepalive_time_ms", 10000),
                ("grpc.keepalive_timeout_ms", 3000),
                ("grpc.keepalive_permit_without_calls", True),
                ("grpc.http2.max_pings_without_data", 0),
                ("grpc.http2.min_time_between_pings_ms", 10000),
                ("grpc.http2.min_ping_interval_without_data_ms", 5000),
            )
        )
        # Add the TurtleSoupGameService to the server.
        servicer = TurtleSoupGameService(conf=conf)
        turtle_soup_game_service_pb2_grpc.add_TurtleSoupGameServiceServicer_to_server(servicer, server)
        # Enable the reflection service.
        if conf["enable_reflection"]:
            SERVICE_NAMES = (
                turtle_soup_game_service_pb2.DESCRIPTOR.services_by_name["TurtleSoupGameService"].full_name,
                reflection.SERVICE_NAME,
            )
            reflection.enable_server_reflection(SERVICE_NAMES, server)
        # Listen on the given address and port.
        server.add_insecure_port("[::]:{}".format(conf["service_port"]))
        # Start the server.
        await server.start()

        # Coroutine to be invoked when the event loop is shutting down.
        async def server_graceful_shutdown():
            loguru_logger.warning("Starting graceful shutdown...")
            # Shuts down the server with 5 seconds of grace period. During the
            # grace period, the server won't accept new connections and allow
            # existing RPCs to continue within the grace period.
            await server.stop(grace=5)
            await servicer.close()
            loguru_logger.info("Stopped TurtleSoupGameService  Server 🤘.")
        _cleanup_coroutines.append(server_graceful_shutdown)

        loguru_logger.info("Server started, listening on [::]:{}".format(conf["service_port"]))
        loguru_logger.info("Started TurtleSoupGameService  Server 🤘.")
        # Wait for the server to be stopped.
        await server.wait_for_termination()
    except Exception as exc:
        loguru_logger.exception("An error occurred while serving the server.")
        raise exc


async def setup_runtime_environment():
    # NOTE: Add your setup code here.
    loguru_logger.debug("Setting up runtime environment...")
    await asyncio.sleep(0)
    loguru_logger.debug("Runtime environment setup completed.")


async def clear_runtime_environment():
    # NOTE: Add your clear code here.
    loguru_logger.debug("Clearing runtime environment...")
    await asyncio.sleep(0)
    loguru_logger.debug("Runtime environment cleared.")


if __name__ == "__main__":
    random.seed(int(time.time()) + random.randrange(10000))

    parse_args()
    conf = get_config()
    init_global_logger(
        service_name=conf["service_name"],
        log_level=conf["log_level"],
        log_printer=conf["log_printer"],
        log_printer_filename=conf["log_printer_filename"]
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(setup_runtime_environment())
    _cleanup_coroutines.append(clear_runtime_environment)

    try:
        loop.run_until_complete(serve(conf=conf))
    except Exception:
        traceback.print_exc()
    finally:
        tasks = []
        if len(_cleanup_coroutines) > 0:
            for co in _cleanup_coroutines:
                tasks.append(asyncio.ensure_future(_cleanup_coroutines()))
        loop.run_until_complete(asyncio.gather(*tasks))
        # NOTE: Wait 250 ms for the underlying connections to close.
        # https://docs.aiohttp.org/en/stable/client_advanced.html#Graceful_Shutdown
        loop.run_until_complete(asyncio.sleep(0.250))
        loop.close()
