#!/usr/bin/env bash

# 遇到执行出错，直接终止脚本的执行
set -o errexit

logger_print()
{
    local prefix="[$(date +%Y/%m/%d\ %H:%M:%S)]"
    echo "${prefix}$@" >&2
}

function run
{
	code_root=github.com/amazingchow/turtle-soup-game-service

	docker run -it --rm --privileged \
		-v ~/.${code_root}:/app \
		-u `id -u` \
		-w /app \
		proto-tools:libprotoc-3.24.3_python-3.8 sh /app/scripts/compile_pb.sh
}

run $@
