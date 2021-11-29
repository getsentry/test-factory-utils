#!/bin/bash

set -euo pipefail

TERRAFORM_STATE_BUCKET="sentryio-terraform"
TERRAFORM_SECTION_FILE="_init.tf"

SCRIPT_NAME=$(basename $0)


function get_configuration_key() {
  grep -A2 backend "${TERRAFORM_SECTION_FILE}" | sed -nr 's/.*(key|prefix).*=.*"(.+)".*/\2/p'
}

function lock_contents() {
    TFLOCK_PATH=$1
    OPERATION='OperationTypeMove'
    INFO="Moving resources between tfstates with tfmv/tfcp"
    WHO="$(whoami)@$(hostname)"
    CREATED=$(date +"%Y-%m-%dT%H:%M:%S.000000Z")
    echo '{"ID":"0","Operation":"'${OPERATION}'","Info":"'${INFO}'","Who":"'${WHO}'","Version":"","Created":"'${CREATED}'","Path":"'${TFLOCK_PATH}'"}'
}

function lock() {
    KEY=$1
    WORKSPACE=$2
    TFLOCK_PATH="gs://${TERRAFORM_STATE_BUCKET}/${KEY}/${WORKSPACE}.tflock"

    echo -ne "Acquiring lock \033[92m${KEY}\x1B[39m \033[91m${WORKSPACE}\x1B[39m: "

    # https://cloud.google.com/storage/docs/generations-preconditions#_Preconditions
    lock_contents ${TFLOCK_PATH} | gsutil -q -h 'x-goog-if-generation-match: 0' cp - "${TFLOCK_PATH}"
    echo "OK"
}

function unlock() {
    KEY=$1
    WORKSPACE=$2
    TFLOCK_PATH="gs://${TERRAFORM_STATE_BUCKET}/${KEY}/${WORKSPACE}.tflock"

    echo -ne "Deleting lock \033[92m${KEY}\x1B[39m \033[91m${WORKSPACE}\x1B[39m: "

    gsutil -q rm "${TFLOCK_PATH}"
    echo "OK"
}


case $SCRIPT_NAME in
  tfcp)
    ACTION="copy"
    ;;
  tfmv)
    ACTION="move"
    ;;
  *)
    echo "This script should not be called directly. Use 'tfcp' or 'tfmv' symlink instead."
    exit 1
    ;;
esac

if [[ $# -lt 3 ]]; then
    echo "Usage: $0 [source-slice] [destination-slice] [resource-1] ... [resource-N]"
    exit 1
fi

PATH1="$(cd "${1}" ; pwd -P)"
PATH2="$(cd "${2}" ; pwd -P)"
shift 2

cd "${PATH1}"
WORKSPACE1=$(terraform workspace show)
KEY1=$(get_configuration_key)

cd "${PATH2}"
WORKSPACE2=$(terraform workspace show)
KEY2=$(get_configuration_key)

echo -e "Going to ${ACTION} \033[94m$@\x1B[39m from \033[92m${KEY1}\x1B[39m (\033[91m${WORKSPACE1}\x1B[39m workspace) to \033[92m${KEY2}\x1B[39m (\033[91m${WORKSPACE2}\x1B[39m workspace)."
echo
echo -e "\033[1mDo you want to perform this action?\x1B[0m"
echo -e "  Only 'yes' will be accepted to approve."
echo
echo -en "  \033[1mEnter a value: \x1B[0m"
read CONFIRMATION
[[ "${CONFIRMATION}" == "yes" ]] || exit 1

# Acquire lock for both states
lock "${KEY1}" "${WORKSPACE1}"
lock "${KEY2}" "${WORKSPACE2}"

cd "${PATH1}"
TFSTATE1="terraform.$(date +%s).tfstate"
terraform state pull > "${TFSTATE1}"

cd "${PATH2}"
TFSTATE2="terraform.$(date +%s).tfstate"
terraform state pull > "${TFSTATE2}"

for ITEM in $@ ; do
    terraform state mv -state="${PATH1}/${TFSTATE1}" -state-out="${PATH2}/${TFSTATE2}" "${ITEM}" "${ITEM}"
done

cd "${PATH2}"
echo -e "Pushing to remote state: \033[92m${KEY2}\x1B[39m \033[91m${WORKSPACE2}\x1B[39m"
terraform state push -lock=false "${TFSTATE2}"

if [[ "${ACTION}" == "move" ]]; then
    cd "${PATH1}"
    echo -e "Pushing to remote state: \033[92m${KEY1}\x1B[39m \033[91m${WORKSPACE1}\x1B[39m"
    terraform state push -lock=false "${TFSTATE1}"
fi

unlock "${KEY2}" "${WORKSPACE2}"
unlock "${KEY1}" "${WORKSPACE1}"
