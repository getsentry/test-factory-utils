export PYTHON_VERSION := python3

.venv:
	$$PYTHON_VERSION -m venv --copies .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

update-docs: .venv
	@echo "Updating ingest-attachments-generator docs"
	.venv/bin/python main.py --update-docs
