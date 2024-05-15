include .env.local .env.secret .env.shared
export

VERSION  := v1.0.0
GIT_HASH := $(shell git rev-parse --short HEAD)
SERVICE  := turtle-soup-game-service
SRC      := $(shell find . -type f -name '*.py' -not -path "./venv/*" -not -path "./internal/proto_gens/*")
CURR_DIR := $(shell pwd)

.PHONY: help
help: ### Display this help screen.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: init
init: ### Initialize the project.
	@pip install -r requirements.txt

.PHONY: deps
deps: ### Update the project dependencies.
	@pip freeze > requirements.txt

.PHONY: pb-fmt
pb-fmt: ### Format the proto files using clang-format (sudo apt install clang-format).
	@clang-format -i ./protos/*.proto

.PHONY: lint
lint: ### Improve your code style. (isort, pyflakes, pycodestyle)
	@echo "Running import sort..."
	@isort --atomic --multi-line=VERTICAL_HANGING_INDENT ${SRC}
	@echo "Running static code analysis..."
	@pyflakes ${SRC}
	@echo "Running code style check..."
	@pycodestyle ${SRC} --ignore=W293,E131,E402,E501

.PHONY: test
test: ### Run your tests.
	@python -m unittest discover -s ./tests -p 'test_*.py'

.PHONY: local_run
local_run: pb-fmt lint ### Run your service locally.
	@python server.py --conf=./etc/${SERVICE}-dev.json 2>&1 | tee dev.log

IMAGE_VERSION := ${VERSION}-${GIT_HASH}

.PHONY: image
image: ### Build your service image.
	@docker build -f ./devops/docker/Dockerfile -t infra-${SERVICE}:${IMAGE_VERSION} .

.PHONY: check_compose
check_compose: ### Check the docker-compose configuration.
	@docker-compose -f "${CURR_DIR}/docker-compose.yml" config

.PHONY: run_compose
run_compose: image check_compose ### Run the application with docker-compose.
	@mkdir -p ~/.infra-config/${SERVICE}
	@cp -f ./etc/${SERVICE}-prod.json ~/.infra-config/${SERVICE}/${SERVICE}.json
	@mkdir -p ${CURR_DIR}/.logs
	@mkdir -p ${CURR_DIR}/.persistent
	@mkdir -p ${CURR_DIR}/.locks
	@mkdir -p ${CURR_DIR}/.shares
	@docker-compose -f "${CURR_DIR}/docker-compose.yml" up -d --build

.PHONY: shutdown_compose
shutdown_compose: ### Shutdown the application with docker-compose.
	@docker-compose -f "${CURR_DIR}/docker-compose.yml" down

now=$(shell date "+%Y%m%d%H%M%S")
.PHONY: logs
logs: ### Show the logs of the running service.
	@docker logs -f infra-${SERVICE} 2>&1 | tee prod_${now}.log
