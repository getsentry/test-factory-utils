#!/usr/bin/env bash
# tf-upg-check.sh
#   Runs TF init & plan with two different versions to make sure the config
#   is compatible with both of them.
#   Since we pin to specific versions, this temporarily comments out the pin
#   and puts it back when finished.

# edit these as needed -- very evralston specific.
# (i keep every version around as ~/bin/terraform-1.2.3)
bin_dir=~/bin  # where you keep your terraform bins
old_ver="0.13.0"
new_ver="0.13.5"

old_bin="${bin_dir}/terraform-${old_ver}"
new_bin="${bin_dir}/terraform-${new_ver}"

if ! [[ -f ./_init.tf ]]; then
    echo "This does not look like an Ops terraform slice. exiting."
    exit 1
fi

cp _init.tf asdf.tf.backup
cat asdf.tf.backup | sed -e "s/required_version/# required_version/" > _init.tf
rm asdf.tf.backup

${old_bin} init
${old_bin} plan

read -p "++++ Press enter to test plan with new version ${new_ver}"

${new_bin} init
${new_bin} plan

if [[ ${?} -ne 0 ]]; then
    echo "Error running 0.13 plan, exiting so it can be fixed"
    echo "Try running '${old_bin} apply' to update state file w/ latest providers."
    exit 1
fi

read -p "++++ Press enter to restore _init.tf or ^C to keep the modifications"

git checkout -- _init.tf
