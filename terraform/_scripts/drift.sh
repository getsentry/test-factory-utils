#!/bin/bash

# Script to get summary about Terraform drift -- difference between Terraform
# description and actual infrastructure. The script iterates over all slices,
# does "terraform plan" and captures the output.
# Usage: ./drift.sh [PROJECT]
# If PROJECT is not specified, then "sentry-st-testing" is used.

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

PROJECT=${1:-"sentry-st-testing"}

function process_slice() {
  if ! terraform init &> /dev/null ; then
    RESULT="ERROR"
    echo -e "\033[91m${RESULT}\x1B[39m"
    return
  fi

  # Note: TERRAFORM_PLAN_OPTS might be useful when running this script from GitHub Actions
  OUTPUT=$(terraform plan ${TERRAFORM_PLAN_OPTS:-} -no-color -detailed-exitcode 2>/dev/null)

  case $? in
    0)
      RESULT="ok"
      echo -e "\033[92m${RESULT}\x1B[39m"
      return
      ;;
    1)
      RESULT="ERROR"
      echo -e "\033[91m${RESULT}\x1B[39m"
      return
      ;;
    2)
      RESULT=$(sed -nr 's/Plan: (.+)/\1/p' <<< "${OUTPUT}")
      echo -e "\033[93m${RESULT}\x1B[39m"
      ;;
  esac
}

for SLICE in $(ls "${SCRIPT_DIR}/../${PROJECT}" | grep -vE '_template|create-slice.sh') ; do
  printf "%-32s        " "${SLICE}"

  cd "${SCRIPT_DIR}/../${PROJECT}/${SLICE}" || exit 1
  process_slice

  # Give a chance to Ctrl+C from script between `terraform plan` runs
  sleep 2
done
