#!/usr/bin/env bash
set +e


{
  rm -r docs/*.md
} > /dev/null 2>&1

cp README.md docs/index.md
cp fakerelay/README.md docs/fakerelay.md
cp helper-images/buildkit/README.md docs/buildkit.md
cp helper-images/topicctl/README.md docs/topicctl.md
cp influxdb-monitor/README.md docs/influxdb-monitor.md
cp ingest-metrics-generator/README.md docs/ingest-metrics-generator.md
cp load-starter/README.md docs/load-starter.md
cp report-generator/README.md docs/report-generator.md
cp report-store/README.md docs/report-store.md
cp stats-collector/README.md docs/stats-collector.md
cp vegeta2influx/README.md docs/vegeta2influx.md
cp workflow-notifier/README.md docs/workflow-notifier.md
