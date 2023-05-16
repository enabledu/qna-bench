.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -Ee -o pipefail

CURRENT_DIR = $(dir $(realpath $(firstword $(MAKEFILE_LIST))))

DOCKER ?= docker
PYTHON ?= python
PP = PYTHONPATH=$(CURRENT_DIR) $(PYTHON)

DATASET = $(abspath dataset/)

all:
	@echo "Pick a target"

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
	$(DOCKER) stop qna-edgedb

stop-docker:
	-$(DOCKER) stop qna-edgedb

docker-clean: stop-docker docker-network-destroy \
	docker-edgedb-volume-destroy

