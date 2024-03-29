_:
	exit 1


run: run-backend

dev-ui: setup-venv setup-frontend
	@echo "Starting backend and front end development server."
	yarn start & FLASK_ENV=development ./.venv/bin/flask run -p 5001

run-frontend: setup-frontend
	yarn start

run-backend: setup-venv
	FLASK_ENV=development  ./.venv/bin/flask run -p 5001

update-ui: setup-frontend
	- rm -r ./build
	- rm -r ./compiled-ui
	yarn build
	mv build compiled-ui

mongo-server:
	docker run \
		--rm \
		-v ${PWD}/.dockervolumes/mongo:/data/db \
		--name mongo-server \
		-p 27017:27017 \
		-it \
		mongo:5.0.6

persistent-mongo-server:
	docker run \
		-d \
		-v ${PWD}/.dockervolumes/mongo:/data/db \
		--name mongo-server \
		-p 27017:27017 \
		mongo:5.0.6


remove-mongo-server:
	docker rm -f mongo-server

mongo-client:
	docker exec -it mongo-server mongo

py-shell: setup-venv
	.venv/bin/ipython -i .ipython/init.py

setup-venv: .venv/bin/python
.PHONY: setup-venv

.venv/bin/python:
	@rm -rf .venv
	python -m venv --copies .venv
	.venv/bin/pip install -U pip wheel
	.venv/bin/pip install -U -r requirements.txt
	.venv/bin/pip install -U -r requirements-dev.txt

format: setup-venv
	.venv/bin/black .

style: setup-venv
	.venv/bin/black --check .

setup-frontend:
	yarn
