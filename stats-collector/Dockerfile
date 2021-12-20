# syntax=docker/dockerfile:1

FROM python:3.8.12-alpine

WORKDIR /app

COPY *.py  requirements.txt ./
COPY flux/ ./flux

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "stats_collector.py"]
