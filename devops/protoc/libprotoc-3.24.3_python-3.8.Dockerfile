FROM python:3.8
RUN printf "\
[global]\n\
timeout = 60\n\
index-url = https://mirrors.aliyun.com/pypi/simple/\n\
trusted-host = mirrors.aliyun.com" \
    > /tmp/pip.conf
ENV PIP_CONFIG_FILE=/tmp/pip.conf
RUN printf "\
googleapis-common-protos==1.60.0\n\
grpcio==1.59.0\n\
grpcio-tools==1.59.0\n\
protobuf==4.24.4" \
    > /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
CMD [ "python", "-m", "grpc_tools.protoc", "--version" ]
