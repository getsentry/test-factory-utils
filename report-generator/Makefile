export PYTHON_VERSION := python3

test:
	py.test ./tests

format:
	black .
	# isort .

lint:
	flake8 .

.venv:
	$$PYTHON_VERSION -m venv --copies .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -U -r requirements.txt


dev-env: .venv
	.venv/bin/pip install -U -r requirements-dev.txt
