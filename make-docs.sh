#!/usr/bin/env bash
set +e


{
  rm -r docs/fakerelay
  rm -r docs/helper-images
  rm -r docs/influxdb-monitor
  rm -r docs/ingest-metrics-generator
  rm -r docs/load-starter
} > /dev/null 2>&1

cp README.md docs/README.md
