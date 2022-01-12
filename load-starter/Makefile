build:
	go mod download && go build
.PHONY: build

dry-run:
	go run . --dry-run --config config.example.yaml --report report.yaml
.PHONY: dry-run

test:
	go test . -v
.PHONY: test

fmt:
	go fmt .
.PHONY: fmt
