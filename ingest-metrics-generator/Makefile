export PYTHON_VERSION := python3

.venv:
	$$PYTHON_VERSION -m venv --copies .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -U -r requirements.txt
