.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -Ee -o pipefail

CURRENT_DIR = $(dir $(realpath $(firstword $(MAKEFILE_LIST))))

DOCKER ?= docker
PSQL ?= psql

PSQL_CMD = $(PSQL) -h localhost -p 3500 -U postgres
PYTHON ?= python
PP = PYTHONPATH=$(CURRENT_DIR) $(PYTHON)

DATASET = $(abspath dataset/data)
users = 100000
comments = 70000
questions = 40000
answers = 30000

all:
	@echo "Pick a target"

new-edgedb-dataset:
	mkdir -p dataset/qna-edgedb
	cat dataset/templates-edgedb/answers.json \
		| sed "s/%ANSWERS%/$(answers)/" > dataset/qna-edgedb/answers.json
	cat dataset/templates-edgedb/comments.json \
		| sed "s/%COMMENTS%/$(comments)/" > dataset/qna-edgedb/comments.json
	cat dataset/templates-edgedb/questions.json \
		| sed "s/%QUESTIONS%/$(questions)/" > dataset/qna-edgedb/questions.json
	cat dataset/templates-edgedb/users.json \
		| sed "s/%USERS%/$(users)/" > dataset/qna-edgedb/users.json
	synth generate dataset/qna-edgedb > $(DATASET)/edbdataset.json

new-postgres-dataset:
	mkdir -p dataset/qna-postgres
	cat dataset/templates-postgres/answers.json \
		| sed "s/%ANSWERS%/$(answers)/" > dataset/qna-postgres/answers.json
	cat dataset/templates-postgres/comments.json \
		| sed "s/%COMMENTS%/$(comments)/" > dataset/qna-postgres/comments.json
	cat dataset/templates-postgres/questions.json \
		| sed "s/%QUESTIONS%/$(questions)/" > dataset/qna-postgres/questions.json
	cat dataset/templates-postgres/users.json \
		| sed "s/%USERS%/$(users)/" > dataset/qna-postgres/users.json
	synth generate dataset/qna-postgres > $(DATASET)/dataset.json

docker-network:
	$(DOCKER) network inspect qna-bench>/dev/null 2>&1 \
		|| $(DOCKER) network create \
			--driver=bridge \
			--opt com.docker.network.bridge.name=br-qna-bench \
			qna-bench

docker-network-destroy:
	$(DOCKER) network inspect qna-bench>/dev/null 2>&1 \
		&& $(DOCKER) network rm qna-bench

docker-edgedb-volume:
	$(DOCKER) volume inspect edgedb-volume >/dev/null 2>&1 \
		|| $(DOCKER) volume create edgedb-volume

docker-edgedb-volume-destroy:
	$(DOCKER) volume inspect edgedb-volume >/dev/null 2>&1 \
		&& $(DOCKER) volume rm edgedb-volume

docker-postgres-volume:
	$(DOCKER) volume inspect postgres-volume >/dev/null 2>&1 \
		|| $(DOCKER) volume create postgres-volume

docker-postgres-volume-destroy:
	$(DOCKER) volume inspect postgres-volume >/dev/null 2>&1 \
		&& $(DOCKER) volume rm postgres-volume

docker-postgres: docker-network docker-postgres-volume
	$(DOCKER) stop qna-postgres >/dev/null 2>&1 || :
	$(DOCKER) run --rm -d --name qna-postgres \
		-v postgres-volume:/var/lib/postgresql/data \
		-e POSTGRES_HOST_AUTH_METHOD=trust \
		--network=qna-bench \
		-p 3500:5432 \
		postgres:14
	sleep 3
	$(DOCKER) exec qna-postgres pg_isready -t10

docker-postgres-stop:
	-$(DOCKER) stop qna-postgres

docker-edgedb: docker-network docker-edgedb-volume
	$(DOCKER) stop qna-edgedb >/dev/null 2>&1 || :
	$(DOCKER) run --rm -d --name qna-edgedb \
		-v edgedb-volume:/var/lib/edgedb/data \
		-e EDGEDB_SERVER_SECURITY=insecure_dev_mode \
		-e EDGEDB_SERVER_ADMIN_UI=enabled \
		--network=qna-bench \
		-p 3000:5656 \
		edgedb/edgedb
	edgedb -H localhost -P 3000 \
		--tls-security=insecure --wait-until-available=120s \
		query "SELECT 'EdgeDB ready'"

docker-edgedb-stop:
	-$(DOCKER) stop qna-edgedb docker-postgres-stop

stop-docker: docker-edgedb-stop 

docker-clean: stop-docker docker-network-destroy \
	docker-edgedb-volume-destroy docker-postgres-volume-destroy

load-edgedb: docker-edgedb
	-edgedb project unlink --non-interactive
	edgedb -H localhost -P 3000 instance link \
		--non-interactive --trust-tls-cert --overwrite edgedb_bench
	edgedb -H localhost -P 3000 project init --link \
		--non-interactive --no-migrations --server-instance edgedb_bench
	edgedb query 'CREATE DATABASE temp'
	edgedb -d temp query 'DROP DATABASE edgedb'
	edgedb -d temp query 'CREATE DATABASE edgedb'
	edgedb query 'DROP DATABASE temp'
	edgedb migrate
	$(PP) -m _edgedb.load_data $(DATASET)/edbdataset.json

load-postgres: docker-postgres-stop reset-postgres
	$(PSQL_CMD) -U postgres_bench -d postgres_bench \
			--file=$(CURRENT_DIR)/_postgres/schema.sql

	$(PP) _postgres/load_data.py $(DATASET)/dataset.json

reset-postgres: docker-postgres
	$(PSQL_CMD) -tc \
		"DROP DATABASE IF EXISTS postgres_bench;"
	$(PSQL_CMD) -U postgres -tc \
		"DROP ROLE IF EXISTS postgres_bench;"
	$(PSQL_CMD) -U postgres -tc \
		"CREATE ROLE postgres_bench WITH \
			LOGIN ENCRYPTED PASSWORD 'edgedbbenchmark';"
	$(PSQL_CMD) -U postgres -tc \
		"CREATE DATABASE postgres_bench WITH OWNER = postgres_bench;"

RUNNER = python bench.py --query get_answer --query get_comments_on_question \
			--query insert_user --query update_comments_on_answer \
			--concurrency 5 --duration 10 --net-latency 1 --async-split 5

run-edgedb:
	$(RUNNER) --html docs/edgedb.html --json docs/edgedb.json edgedb_py_sync edgedb_py_async

run-postgres:
	$(RUNNER) --html docs/postgres.html --json docs/postgres.json postgres_py_sync