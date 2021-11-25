load-starter-docker:
	cd load-starter; \
	docker build --target final -f Dockerfile -t load-starter . && docker run --name load-starter load-starter

.PHONY: load-starter-docker