build:
	go mod download && go build
.PHONY: build

dry-run:
	go run . --dry-run
.PHONY: dry-run

test:
	go test . -v
.PHONY: test

fmt:
	go fmt .
.PHONY: fmt

update-docs:
	@echo "Updating influxdb-monitor docs"
	go run . update-docs
