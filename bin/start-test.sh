#!/usr/bin/env bash
set -euo pipefail

### Just a mock for now. First we need to build an image with Python stuff we want to run.

IMAGE="busybox:1.32"

DATE="$(date -u '+%Y-%m-%d-%H-%M-%S')"
RANDOM_ID="$(</dev/urandom LC_ALL=C tr -dc '0-9' | head -c 4 || true)"
NAME="load-test-${DATE}-${RANDOM_ID}"

TEMPLATE=$(cat <<END_HEREDOC
apiVersion: batch/v1
kind: Job
metadata:
  name: ${NAME}
  labels:
    service: run-test
spec:
  template:
    spec:
      containers:
      - name: test
        image: ${IMAGE}
        command: ["sleep", "60"]
      restartPolicy: Never
  backoffLimit: 3
END_HEREDOC
)

echo "${TEMPLATE}" | sentry-kube kubectl apply -f -
