#!/usr/bin/env bash
set -euo pipefail

SCRIPT_ARGS=( "$@" )
SCRIPT_ARGS_LEN="$#"

update_relay() {
  # It's super annoying to do arg parsing in bash, so delegating to a small Python script for now
  RELAY_VERSION="$(python extract-relay-version.py "${SCRIPT_ARGS[@]}" 2>/dev/null)"

  if [ -z "${RELAY_VERSION}" ]; then
    echo '>>> Cannot find relay version, exiting!'
    exit 1
  fi

  RELAY_IMAGE="us.gcr.io/sentryio/relay:${RELAY_VERSION}"

  echo ">>> New Relay version: '${RELAY_VERSION}'. Updating..."
  sentry-kube kubectl -q set image deployment relay-main "relay=${RELAY_IMAGE}"

  sleep 1

  echo ">>> Waiting for the rollout to finish..."
  if ! sentry-kube kubectl -q rollout status deployment --timeout=1m relay-main; then
    echo ">>> Something went wrong. Check relay deployment."
    exit 1
  fi
}


start_test_job() {
  IMAGE="busybox:1.32"
  DATE="$(date -u '+%Y-%m-%d-%H-%M-%S')"
  RANDOM_ID="$(</dev/urandom LC_ALL=C tr -dc '0-9' | head -c 4 || true)"
  NAME="load-test-${DATE}-${RANDOM_ID}"

  if [ "${SCRIPT_ARGS_LEN}" -ge 1 ]; then
    # Form a JSON list from script arguments
    CONTAINER_ARGS="[$(printf '"%s", ' "${SCRIPT_ARGS[@]}")]"
  else
    CONTAINER_ARGS="[]"
  fi

  TEMPLATE=$(cat <<END_HEREDOC
---
apiVersion: v1
kind: Pod
metadata:
  name: ${NAME}
  labels:
    service: "start-test"
    startedby: "${USER}"
spec:
  containers:
    - name: test
      image: "${IMAGE}"
      command: ["echo"]
      args: ${CONTAINER_ARGS}
  restartPolicy: Never
END_HEREDOC
  )

  echo ">>> Scheduling a test run..."
  echo "${TEMPLATE}" | sentry-kube kubectl -q apply -f -
}

if ! command -v sentry-kube &> /dev/null; then
  echo "sentry-kube not found, exiting."
  exit 1
fi

update_relay
start_test_job
