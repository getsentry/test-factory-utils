#!/usr/bin/env bash
set -euo pipefail

SCRIPT_ARGS=( "$@" )
SCRIPT_ARGS_LEN="$#"

update_relay() {
  RELAY_VERSION=""

  # Extract relay version from the script arguments
  while getopts ":v:" opt "${SCRIPT_ARGS[@]}"; do
    case ${opt} in
      v)
        RELAY_VERSION="${OPTARG}"
        break
        ;;
      *)
        ;;
    esac
  done

  # FIXME this doesn't handle long options, and also doesn't work if there are args before "-v"

  if [ -z "${RELAY_VERSION}" ]; then
    echo '>>> Cannot find relay version, exiting!'
    exit 1
  fi

  RELAY_IMAGE="us.gcr.io/sentryio/relay:${RELAY_VERSION}"

  echo ">>> Updating Relay's version..."
  sentry-kube kubectl set image deployment relay-main "relay=${RELAY_IMAGE}"

  sleep 1

  echo ">>> Waiting for the rollout to finish..."
  sentry-kube kubectl rollout status deployment relay-main
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
  echo "${TEMPLATE}" | sentry-kube kubectl apply -f -
}


update_relay
start_test_job
