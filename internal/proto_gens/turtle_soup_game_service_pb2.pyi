from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LLMEngine(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    OPENAI: _ClassVar[LLMEngine]
    AZURE: _ClassVar[LLMEngine]
    GEMINI: _ClassVar[LLMEngine]
    CLAUDE: _ClassVar[LLMEngine]
OPENAI: LLMEngine
AZURE: LLMEngine
GEMINI: LLMEngine
CLAUDE: LLMEngine

class PingRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class PongResponse(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class AIResult(_message.Message):
    __slots__ = ["code", "msg"]
    CODE_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    code: int
    msg: str
    def __init__(self, code: _Optional[int] = ..., msg: _Optional[str] = ...) -> None: ...

class GenerateDialogueRequest(_message.Message):
    __slots__ = ["conversation_id", "llm_engine", "conversation_system_prompt", "to_reply_for_general_question", "chat", "ext_thread_id", "ext_uid", "ext_nickname"]
    CONVERSATION_ID_FIELD_NUMBER: _ClassVar[int]
    LLM_ENGINE_FIELD_NUMBER: _ClassVar[int]
    CONVERSATION_SYSTEM_PROMPT_FIELD_NUMBER: _ClassVar[int]
    TO_REPLY_FOR_GENERAL_QUESTION_FIELD_NUMBER: _ClassVar[int]
    CHAT_FIELD_NUMBER: _ClassVar[int]
    EXT_THREAD_ID_FIELD_NUMBER: _ClassVar[int]
    EXT_UID_FIELD_NUMBER: _ClassVar[int]
    EXT_NICKNAME_FIELD_NUMBER: _ClassVar[int]
    conversation_id: str
    llm_engine: LLMEngine
    conversation_system_prompt: str
    to_reply_for_general_question: bool
    chat: str
    ext_thread_id: str
    ext_uid: str
    ext_nickname: str
    def __init__(self, conversation_id: _Optional[str] = ..., llm_engine: _Optional[_Union[LLMEngine, str]] = ..., conversation_system_prompt: _Optional[str] = ..., to_reply_for_general_question: bool = ..., chat: _Optional[str] = ..., ext_thread_id: _Optional[str] = ..., ext_uid: _Optional[str] = ..., ext_nickname: _Optional[str] = ...) -> None: ...

class GenerateDialogueResponse(_message.Message):
    __slots__ = ["ret", "conversation_id", "chat", "ext_thread_id", "ext_uid"]
    RET_FIELD_NUMBER: _ClassVar[int]
    CONVERSATION_ID_FIELD_NUMBER: _ClassVar[int]
    CHAT_FIELD_NUMBER: _ClassVar[int]
    EXT_THREAD_ID_FIELD_NUMBER: _ClassVar[int]
    EXT_UID_FIELD_NUMBER: _ClassVar[int]
    ret: AIResult
    conversation_id: str
    chat: str
    ext_thread_id: str
    ext_uid: str
    def __init__(self, ret: _Optional[_Union[AIResult, _Mapping]] = ..., conversation_id: _Optional[str] = ..., chat: _Optional[str] = ..., ext_thread_id: _Optional[str] = ..., ext_uid: _Optional[str] = ...) -> None: ...
