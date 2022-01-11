#!/usr/bin/env bash
### This script runs "stats-collector" on the default cluster
set -euo pipefail

IMAGE="europe-west3-docker.pkg.dev/sentry-st-testing/main/stats-collector:564f1c27eae1d05726b96b5f583c74bc7828d4a1"

INFLUX_URL=${INFLUX_URL:-http://influxdb-server.default.svc.cluster.local}

# FIXME: arguments are not propagated properly because sentry-kube consumes '--'
sentry-kube kubectl run "stats-collector-$(whoami)-${RANDOM}" \
    -it \
    --rm \
    --image="${IMAGE}" \
    --restart=Never \
    --env "INFLUX_URL=${INFLUX_URL}" \
    -- \
    -- \
    "$@"
