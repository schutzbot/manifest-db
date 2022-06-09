#!/bin/bash
set -euxo pipefail

# set locale to en_US.UTF-8
sudo dnf install -y glibc-langpack-en git make jq
localectl set-locale LANG=en_US.UTF-8

# Colorful output.
function greenprint {
    echo -e "\033[1;32m[$(date -Isecond)] ${1}\033[0m"
}

function setup_repo {
  local project=$1
  local commit=$2
  local priority=${3:-10}

  local REPO_PATH=${project}/${DISTRO_VERSION}/${ARCH}/${commit}
  if [[ "${NIGHTLY:=false}" == "true" && "${project}" == "osbuild-composer" ]]; then
    REPO_PATH=nightly/${REPO_PATH}
  fi

  greenprint "Setting up dnf repository for ${project} ${commit}"
  sudo tee "/etc/yum.repos.d/${project}.repo" << EOF
[${project}]
name=${project} ${commit}
baseurl=http://osbuild-composer-repos.s3-website.us-east-2.amazonaws.com/${REPO_PATH}
enabled=1
gpgcheck=0
priority=${priority}
EOF
}

# Get OS details.
source /etc/os-release
ARCH=$(uname -m)
DISTRO_CODE="${DISTRO_CODE:-${ID}-${VERSION_ID//./}}"
OSBUILD_GIT_COMMIT=$(cat Schutzfile | jq -r '.["'"${ID}-${VERSION_ID}"'"].dependencies.osbuild.commit')

if [[ $ID == "rhel" && ${VERSION_ID%.*} == "9" ]]; then
  # There's a bug in RHEL 9 that causes /tmp to be mounted on tmpfs.
  # Explicitly stop and mask the mount unit to prevent this.
  # Otherwise, the tests will randomly fail because we use /tmp quite a lot.
  # See https://bugzilla.redhat.com/show_bug.cgi?id=1959826
  greenprint "Disabling /tmp as tmpfs on RHEL 9"
  sudo systemctl stop tmp.mount && sudo systemctl mask tmp.mount
fi

if [[ $ID == "centos" && $VERSION_ID == "8" ]]; then
    # Workaround for https://bugzilla.redhat.com/show_bug.cgi?id=2065292
    # Remove when podman-4.0.2-2.el8 is in Centos 8 repositories
    greenprint "Updating libseccomp on Centos 8"
    sudo dnf upgrade -y libseccomp
fi

# Distro version that this script is running on.
DISTRO_VERSION=${ID}-${VERSION_ID}

if [[ "$ID" == rhel ]] && sudo subscription-manager status; then
  # If this script runs on subscribed RHEL, install content built using CDN
  # repositories.
  DISTRO_VERSION=rhel-${VERSION_ID%.*}-cdn

  # workaround for https://github.com/osbuild/osbuild/issues/717
  sudo subscription-manager config --rhsm.manage_repos=1
fi

greenprint "Enabling fastestmirror to speed up dnf 🏎️"
echo -e "fastestmirror=1" | sudo tee -a /etc/dnf/dnf.conf

OSBUILD_GIT_COMMIT=$(cat Schutzfile | jq -r '.["'"${ID}-${VERSION_ID}"'"].dependencies.osbuild.commit')
if [[ "${OSBUILD_GIT_COMMIT}" != "null" ]]; then
  setup_repo osbuild "${OSBUILD_GIT_COMMIT}" 10
fi

sudo dnf install -y osbuild*

sudo dnf install -y python3-pip
pip3 show osbuild

greenprint "OSBuild installed"
