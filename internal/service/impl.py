# -*- coding: utf-8 -*-
import asyncio
import hashlib
import os
import random
import time
from typing import Any, Dict, Optional

import aiohttp
import grpc.aio
import openai
import ujson as json
from loguru import logger as loguru_logger

from internal.classes.singleton import Singleton
from internal.proto_gens import (
    turtle_soup_game_service_pb2,
    turtle_soup_game_service_pb2_grpc
)
from internal.utils.helper import timeit
from internal.utils.http_tracing import http_trace_config
from internal.utils.openai_tools import acall_chat_completion_api_with_backoff


class TurtleSoupGameServiceSetupException(Exception):
    pass


class TurtleSoupGameService(turtle_soup_game_service_pb2_grpc.TurtleSoupGameServiceServicer, metaclass=Singleton):

    def __init__(
        self,
        *,
        conf: Optional[Dict[str, Any]] = None
    ):
        openai_key_list = os.getenv("OPENAI_KEY_LIST")
        if openai_key_list is None or len(openai_key_list) == 0:
            raise TurtleSoupGameServiceSetupException("Please set env for OPENAI_KEY_LIST.")

        openai.log = "info"
        # To make async openai requests more efficient.
        openai.aiosession.set(aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=32),
            connector_owner=True,
            timeout=aiohttp.ClientTimeout(total=60),
            trace_configs=[http_trace_config]
        ))
        if "enable_http_proxy" in conf["openai"] and conf["openai"]["enable_http_proxy"]:
            openai.proxy = conf["openai"]["http_proxy"]

        self._env = conf["deployment_env"]
        self._openai_conf_intention_model = conf["openai"]["intention_model"]
        self._openai_conf_intention_model_version = conf["openai"]["intention_model_version"]
        self._openai_conf_chat_model = conf["openai"]["chat_model"]
        self._openai_conf_chat_model_version = conf["openai"]["chat_model_version"]
        self._openai_key_list = openai_key_list.split(",")
        self._openai_conf_chat_model_max_tokens = int((4096 - 4 - 128) * 0.95)
        self._openai_conf_chat_enable_memory = conf["openai"]["enable_memory"]

    async def close(self):
        session = openai.aiosession.get()
        if session is not None:
            await session.close()
        else:
            await asyncio.sleep(0)

    @staticmethod
    def new_conversation_id(uid: str = "None", rid: str = "None") -> str:
        return hashlib.md5(f"{uid}.{rid}.{time.time()}.{random.randint(0, 10000)}".encode()).hexdigest()

    @timeit
    async def Ping(
        self,
        request: turtle_soup_game_service_pb2.PingRequest,
        context: grpc.aio.ServicerContext
    ):
        resp = turtle_soup_game_service_pb2.PongResponse()

        metadata = dict(context.invocation_metadata())
        trace_id = metadata.get("x-request-id", "None")
        span_id = ""

        with loguru_logger.contextualize(trace_id=trace_id, span_id=span_id):
            loguru_logger.debug("Ping")
            return resp

    @timeit
    async def GenerateDialogue(
        self,
        request: turtle_soup_game_service_pb2.GenerateDialogueRequest,
        context: grpc.aio.ServicerContext
    ):
        resp = turtle_soup_game_service_pb2.GenerateDialogueResponse()

        metadata = dict(context.invocation_metadata())
        uid = metadata.get("x-uid", "None")
        trace_id = metadata.get("x-request-id", "None")
        conversation_id = request.conversation_id
        if len(conversation_id) == 0:
            conversation_id = self.new_conversation_id(uid, trace_id)
        span_id = conversation_id

        with loguru_logger.contextualize(trace_id=trace_id, span_id=span_id):
            loguru_logger.debug("Entering GenerateDialogue method context...")

            system_prompt = request.conversation_system_prompt.strip()
            user_message = request.chat.strip()

            reply = ""
            try:
                st = time.time()
                try:
                    loguru_logger.debug(f"ChatCompletion.Model:{self._openai_conf_chat_model} ChatCompletion.SystemPrompt:\n")
                    loguru_logger.debug(f"\n{system_prompt}")
                    loguru_logger.debug(f"ChatCompletion.Model:{self._openai_conf_chat_model} ChatCompletion.UserMessage:\n")
                    loguru_logger.debug(f"\n{user_message}")

                    openai_key = self._openai_key_list[random.randint(0, len(self._openai_key_list) - 1)]
                    if request.to_reply_for_general_question:
                        response_format = {"type": "text"}
                    else:
                        response_format = {"type": "json_object"}
                    
                    chat_completion = await acall_chat_completion_api_with_backoff(
                        api_key=openai_key,
                        messages=[
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            {
                                "role": "user",
                                "content": user_message
                            }
                        ],
                        model=self._openai_conf_chat_model,
                        frequency_penalty=0.0,
                        presence_penalty=0.0,
                        temperature=1.0,
                        max_tokens=256,
                        n=1,
                        top_p=1.0,
                        response_format=response_format,
                        timeout=60,
                    )
                    total_tokens = chat_completion.usage.total_tokens
                    prompt_tokens = chat_completion.usage.prompt_tokens
                    completion_tokens = chat_completion.usage.completion_tokens
                    loguru_logger.debug(f"Used total_tokens: {total_tokens}, prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}.")
                    
                    loguru_logger.debug(f"OpenAI LLM Response:\n{chat_completion}")
                    _reply = chat_completion.choices[0].message.content
                    loguru_logger.debug(f"OpenAI LLM Reply:\n{_reply}")
                    if request.to_reply_for_general_question:
                        reply = _reply
                    else:
                        reply = json.loads(_reply)["result"]
                except Exception as exc:
                    loguru_logger.error(f"Failed to invoke OpenAI LLM, err:{exc}.")
                finally:
                    ed = time.time()
                    loguru_logger.debug(f"OpenAI LLM Calling used {ed - st:.3f}s.")

                resp.ret.code = 0
                resp.ret.msg = "OK"
                if len(reply) == 0:
                    resp.ret.code = 10500
                    resp.ret.msg = "Failed to invoke OpenAI LLM"
                resp.conversation_id = conversation_id
                resp.chat = reply
                resp.ext_thread_id = request.ext_thread_id
                resp.ext_uid = uid
            except Exception as exc:
                loguru_logger.error(f"GenerateDialogue RPC Method Internal Error, err:{exc}")
                resp.ret.code = 10500
                resp.ret.msg = f"GenerateDialogue RPC Method Internal Error, err:{exc}"
            finally:
                return resp
