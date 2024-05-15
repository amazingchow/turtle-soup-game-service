# -*- coding: utf-8 -*-
import os
import sys
from typing import Any, Dict

import ujson as json
from loguru import logger as loguru_logger


def _env(key, type_, default=None):
    if key not in os.environ:
        return default

    val = os.environ[key]

    if type_ == str:
        return val
    elif type_ == bool:
        if val.lower() in ["1", "true", "yes", "y", "ok", "on"]:
            return True
        if val.lower() in ["0", "false", "no", "n", "nok", "off"]:
            return False
        raise ValueError(
            "Invalid environment variable '%s' (expected a boolean): '%s'" % (key, val)
        )
    elif type_ == int:
        try:
            return int(val)
        except ValueError:
            raise ValueError(
                "Invalid environment variable '%s' (expected an integer): '%s'" % (key, val)
            ) from None


def custom_serialize_record(text: str, record: Dict[str, Any]) -> str:
    serializable = {
        "service_name": record["extra"]["service_name"],
        "trace_id": record["extra"]["trace_id"],
        "span_id": record["extra"]["span_id"],
        "ts": text[3:26],
        "msg": text[31:]
    }
    return json.dumps(serializable, default=str, ensure_ascii=False) + "\n"


def init_global_logger(
    *,
    service_name: str = "",
    log_level: str = "debug",
    log_printer: str = "console",
    log_printer_filename: str = "",
):
    # remove default logger
    loguru_logger.remove()
    if log_printer.lower() == "disk" and len(log_printer_filename) > 0:
        # loguru_logger.configure() must be called before loguru_logger.add()
        loguru_logger.configure(extra={
            "service_name": service_name, "trace_id": "", "span_id": ""
        })
        if _env("LOGURU_SERIALIZE", bool, False):
            # add new logger
            handler_id = loguru_logger.add(
                sink=log_printer_filename,
                level=log_level.upper(),
                format="<green>ts={time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
                    "<level>msg={message}</level>",
                colorize=_env("LOGURU_COLORIZE", bool, False),
                serialize=True,
                backtrace=_env("LOGURU_BACKTRACE", bool, True),
                diagnose=_env("LOGURU_DIAGNOSE", bool, True),
                enqueue=_env("LOGURU_ENQUEUE", bool, False),
                catch=_env("LOGURU_CATCH", bool, True),
                rotation="64 MB"
            )
            # override _serialize_record method
            loguru_logger._core.handlers[handler_id]._serialize_record = custom_serialize_record
        else:
            loguru_logger.add(
                sink=log_printer_filename,
                level=log_level.upper(),
                format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                    "<level>{level: <8}</level> | "
                    "<red>service_name={extra[service_name]}</red> <red>trace_id={extra[trace_id]}</red> <red>span_id={extra[span_id]}</red> | "
                    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                    "- <level>{message}</level>",
                colorize=_env("LOGURU_COLORIZE", bool, False),
                serialize=_env("LOGURU_SERIALIZE", bool, False),
                backtrace=_env("LOGURU_BACKTRACE", bool, True),
                diagnose=_env("LOGURU_DIAGNOSE", bool, True),
                enqueue=_env("LOGURU_ENQUEUE", bool, False),
                catch=_env("LOGURU_CATCH", bool, True),
                rotation="64 MB"
            )
    else:
        # loguru_logger.configure() must be called before loguru_logger.add()
        loguru_logger.configure(extra={
            "service_name": service_name, "trace_id": "", "span_id": ""
        })
        # add new logger
        loguru_logger.add(
            sink=sys.stderr,
            level=log_level.upper(),
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<red>service_name={extra[service_name]}</red> <red>trace_id={extra[trace_id]}</red> <red>span_id={extra[span_id]}</red> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "- <level>{message}</level>",
            colorize=_env("LOGURU_COLORIZE", bool, False),
            serialize=False,
            backtrace=_env("LOGURU_BACKTRACE", bool, True),
            diagnose=_env("LOGURU_DIAGNOSE", bool, True),
            enqueue=_env("LOGURU_ENQUEUE", bool, False),
            catch=_env("LOGURU_CATCH", bool, True),
        )
