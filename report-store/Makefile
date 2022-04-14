_:
	exit 1

run: setup-venv setup-frontend
	yarn start & FLASK_ENV=development ./.venv/bin/flask run -p 5050

run-frontend: setup-frontend
	yarn start

run-backend: setup-venv
	FLASK_ENV=development ./.venv/bin/flask run -p 5050

mongo-server:
	docker run \
		--rm \
		-v ${PWD}/.dockervolumes/mongo:/data/db \
		--name mongo-server \
		-p 27017:27017 \
		-it \
		mongo:5.0.6

mongo-client:
	docker exec -it mongo-server mongo

py-shell:
	ipython -i .ipython/init.py

setup-venv: .venv/bin/python
.PHONY: setup-venv

.venv/bin/python:
	@rm -rf .venv
	python -m venv --copies .venv
	.venv/bin/pip install -U pip wheel
	.venv/bin/pip install -U -r requirements.txt

format: setup-venv
	.venv/bin/black .

style: setup-venv
	.venv/bin/black --check .


setup-frontend:
	yarn
