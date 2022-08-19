build: lint
	go mod download && go build
.PHONY: build

dry-run:
	go run . --dry-run --config ./examples/config.example.py --report report.yaml
.PHONY: dry-run

test:
	go test . -v
.PHONY: test

fmt:
	go fmt .
.PHONY: fmt

lint:
	go vet .
.PHONY: lint

update-docs:
	@echo "Updating load-starter docs"
	go run . update-docs
