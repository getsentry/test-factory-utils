#!/usr/bin/env bash
### This script runs "stats-collector" on the default cluster
set -euo pipefail

IMAGE="europe-west3-docker.pkg.dev/sentry-st-testing/main/stats-collector:6d8216178208c4f2df812c6ddd8b3c9522b6242a"
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
