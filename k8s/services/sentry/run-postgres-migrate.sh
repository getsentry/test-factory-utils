#!/usr/bin/env bash
set -euxo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}"

# IMAGE_NAME="$(yq e .image_name _values.yaml)"
# IMAGE_TAG="$(yq e .image_tag _values.yaml)"
# IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"

# Recreate the database
sentry-kube kubectl run "postgres-migrate-$(whoami)-${RANDOM}" \
    -it \
    --rm \
    --image=postgres:13-alpine \
    --restart=Never \
    -- \
    -- psql \
        -h postgres-sentry.default.svc.cluster.local \
        -U postgres \
        -c 'DROP DATABASE IF EXISTS sentry;' \
        -c 'CREATE DATABASE sentry;'

# Run the migration
echo y | \
    sentry-kube run-pod \
        -d ingest-metrics-consumer \
        -s sentry \
        -c ingest-metrics-consumer \
        --args '["upgrade", "--noinput"]'
