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

generate-docs:
	cd ingest-metrics-generator && $(MAKE) update-docs
	cd load-starter && $(MAKE) update-docs
	cd influxdb-monitor && $(MAKE) update-docs
	cd vegeta2influx && $(MAKE) update-docs
	-rm -rf docs/
	-mkdir docs
	-cp README.md docs/index.md
	-cp fakerelay/README.md docs/fakerelay.md
	-cp helper-images/buildkit/README.md docs/buildkit.md
	-cp helper-images/topicctl/README.md docs/topicctl.md
	-cp influxdb-monitor/README.md docs/influxdb-monitor.md
	-cp ingest-metrics-generator/README.md docs/ingest-metrics-generator.md
	-cp load-starter/README.md docs/load-starter.md
	-cp report-generator/README.md docs/report-generator.md
	-cp report-store/README.md docs/report-store.md
	-cp stats-collector/README.md docs/stats-collector.md
	-cp vegeta2influx/README.md docs/vegeta2influx.md
	-cp workflow-notifier/README.md docs/workflow-notifier.md

local-docs:
	cd docs; \
	bundle exec jekyll serve
