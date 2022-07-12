# syntax=docker/dockerfile:1

FROM python:3.8.12-alpine

RUN apk --no-cache add bash

WORKDIR /app

# Install requirements first to optimize layer caching
COPY requirements.txt ./
RUN pip install -r requirements.txt --no-cache-dir

COPY *.py ./


ENTRYPOINT ["python", "report_generator.py"]
