#!/usr/bin/env bash

# 遇到执行出错，直接终止脚本的执行
set -o errexit

logger_print()
{
    local prefix="[$(date +%Y/%m/%d\ %H:%M:%S)]"
    echo "${prefix}$@" >&2
}

function test_rpc_methods
{
    system_prompt=$(<./turtle_soup_game_chat_system_prompt.txt)
    logger_print "system_prompt: " $system_prompt

    grpcurl \
        -rpc-header x-uid:1000003 \
        -rpc-header x-request-id:73338239da584998aca91639651334fa \
        -d @ -plaintext -emit-defaults \
        localhost:16869 turtle_soup_game_service.TurtleSoupGameService/GenerateDialogue << EOM
{
    "llm_engine": 0,
    "conversation_system_prompt": "# Role: 真相判断专家 ## 任务 请判断下述<真相>是否完整概括了<关键线索>中的所有条目。 输出是否完整的判断结果（Result）和对应的解释原因（Reason）。 注意仅通过给出的<关键线索>进行判断，不要参考其他隐藏信息。 <真相>的表达方式可以和<关键线索>不一样，只要含义正确即可。 ### Result - 如果完整概括，则回答“猜测成功”。 - 如果没有完整概括，则回答“很接近了”。 - 如果用<真相>和<关键线索>相关度较低，则回答“猜得不对”。 ### Reason 你得出 Result 的原因，真相是否完整、不完整时缺少的关键线索等。 ## 输出格式 确保按如下 JSON 格式输出： '''JSON { \"result\": \"很接近了，但还有一些细节没有推断出来。\", \"reason\": \"判断原因\" } ''' ## 真相 我是植物大战僵尸里的向日葵，相继死去的伙伴是其他植物。 ## 关键线索 - 背景是植物大战僵尸 - 我是植物 ## 注意事项 - 如果用户直接询问结果或具体原因，你应该告诉用户“你需要自己进行猜测”。 - 请反复、仔细检查你的回复，避免回答错误给用户造成不好的体验。",
    "to_reply_for_general_question": false,
    "chat": "我是植物大战僵尸里的向日葵",
    "ext_thread_id": "t000041",
    "ext_uid": "1000003",
    "ext_nickname": "adamzhou.eth"
}
EOM
}

function run
{
    grpcurl -plaintext localhost:16869 list turtle_soup_game_service.TurtleSoupGameService
    test_rpc_methods
}

run $@
