#!/usr/bin/env bash

# 遇到执行出错，直接终止脚本的执行
set -o errexit

logger_print()
{
    local prefix="[$(date +%Y/%m/%d\ %H:%M:%S)]"
    echo "${prefix}$@" >&2
}

run()
{
	src_dir=/app/protos
	api_dir=/app/internal/proto_gens
	mkdir -p ${api_dir}
	for i in $(ls ${src_dir}/*.proto); do
		logger_print "[INFO]" "to compile ${i}..."
		python -m grpc_tools.protoc -I${src_dir} --python_out=${api_dir} --pyi_out=${api_dir} --grpc_python_out=${api_dir} "${i}"
		logger_print "[INFO]" "compiled ${i}."
	done
}

run $@
