# syntax=docker/dockerfile:1

FROM python:3.8.12-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install requirements first to optimize layer caching
COPY requirements.txt ./
RUN pip install -r requirements.txt --no-cache-dir

COPY *.py ./

ENTRYPOINT ["python", "report_generator.py"]
