#!/usr/bin/env bash
# The script generates a new terraform slice in the same directory, based on the template in _template/
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

create_slice_dir() {
    local SLICE="$1"
    cp -R _template "${SLICE}"

    cd "${SLICE}"

    # Replace all "FIX ME" markers
    find . \( -name '*.tf' -o -name 'README.md' \) -type f -exec perl -i -pe "s/FIX\\\nME/${SLICE}/;" {} \;

    # Delete template comments
    find . -name '*.tf' -type f -exec perl -i -pe "s/ # _TEMPLATE:.*//;" {} \;

    # Update README.md
    README_CONTENTS="$(head -n 1 README.md)\n\nFIXME!"
    echo -e "${README_CONTENTS}" > README.md
}

cd "${SCRIPT_DIR}"

SLICE_NAME="${1:-}"

if [[ $(basename "${SCRIPT_DIR}") == "_scripts" ]]; then
    echo 'Do not run this script directly, use the symlinks in the project folders (for example, in "terraform/sentry-st-testing")'
    exit 1
fi

if [[ ${SLICE_NAME} == "" ]]; then
    echo 'Please specify the new slice name.'
    exit 1
fi

if [[ -f "${SLICE_NAME}" || -d "${SLICE_NAME}" ]]; then
    echo "'${SLICE_NAME}' file or directory exists, aborting."
    exit 1
fi

if [[ ${SLICE_NAME} =~ [=/.+] || ${SLICE_NAME} =~ ^- ]]; then
    echo "Invalid slice name, aborting."
    exit 1
fi

create_slice_dir "${SLICE_NAME}"
echo "The new slice has been created: ${SCRIPT_DIR}/${SLICE_NAME}"
