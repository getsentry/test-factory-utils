#!/usr/bin/env bash
set -euo pipefail

echo ">>> Removing all completed pods..."
sentry-kube kubectl --yes --quiet delete pod --field-selector='status.phase==Succeeded' -l service=start-test
