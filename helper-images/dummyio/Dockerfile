FROM python:3.11-slim as builder

RUN python -m venv .venv
COPY requirements.txt .
RUN .venv/bin/pip install -r requirements.txt

FROM python:3.11-slim

COPY --from=builder /.venv /.venv
ENV PATH /.venv/bin:$PATH

WORKDIR /app
COPY app.py .

EXPOSE 3000

ENTRYPOINT [ "granian" ]
CMD [ "--host", "0.0.0.0", "--port", "3000", "app:app" ]
