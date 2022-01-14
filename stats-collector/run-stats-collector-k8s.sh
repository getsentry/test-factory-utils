#!/usr/bin/env bash
### This script runs "stats-collector" on the default cluster
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}"

IMAGE_NAME="europe-west3-docker.pkg.dev/sentry-st-testing/main/stats-collector"
IMAGE="$(grep ${IMAGE_NAME} ../k8s/services/workflows/z-run-test.yaml | awk '{print $2}')"
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
