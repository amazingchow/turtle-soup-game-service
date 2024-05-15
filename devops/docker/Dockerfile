FROM python:3.8.18-slim-bullseye
WORKDIR /app
RUN printf "\
[global]\n\
timeout = 60\n\
index-url = https://mirrors.aliyun.com/pypi/simple/\n\
trusted-host = mirrors.aliyun.com" \
    > /tmp/pip.conf
ENV PIP_CONFIG_FILE=/tmp/pip.conf
COPY ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY . /app
RUN mkdir -p /app/config /app/logs /app/persistent /app/locks /app/shares
EXPOSE 16869
CMD [ \
    "python", \
    "/app/server.py", \
    "--conf=/app/config/turtle-soup-game-service.json" \
]
