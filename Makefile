load-starter-docker:
	cd load-starter; \
	docker build --target final -f Dockerfile -t load-starter . && docker run --name load-starter load-starter

.PHONY: load-starter-docker

push-load-starter:
	cd load-starter; \
	./push-image.sh

.PHONY: push-load-starter

push-stats-collector:
	cd stats-colector; \
	./push-image.sh

.PHONY: push-stats-collector

push-ingest-metrics-generator:
	cd ingest-metrics-generator; \
	./push-image.sh

.PHONY: push-ingest-metrics-generator

push-influxdb-monitor:
	cd influxdb-monitor; \
	./push-image.sh

.PHONY: push-influxdb-monitor

push-all: push-influxdb-monitor push-ingest-metrics-generator push-load-starter push-stats-collector

.PHONY: push-all


local-docs:
	cd docs; \
	bundle exec jekyll serve
