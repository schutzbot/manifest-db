#!/bin/bash
set -euxo pipefail

sudo dnf install -y jq


DNF_REPO_BASEURL=http://osbuild-composer-repos.s3.amazonaws.com

OSBUILD_COMMIT=$(jq -r '.global.dependencies.osbuild.commit' Schutzfile)

# Get OS details.
source /etc/os-release
ARCH=$(uname -m)

# Add osbuild team ssh keys.
cat schutzbot/team_ssh_keys.txt | tee -a ~/.ssh/authorized_keys > /dev/null

# Distro version that this script is running on.
DISTRO_VERSION=${ID}-${VERSION_ID}

if [[ "$ID" == rhel ]] && sudo subscription-manager status; then
  # If this script runs on subscribed RHEL, install content built using CDN
  # repositories.
  DISTRO_VERSION=rhel-${VERSION_ID%.*}-cdn
fi

# Set up dnf repositories with the RPMs we want to test
sudo tee /etc/yum.repos.d/osbuild.repo << EOF
[osbuild]
name=osbuild ${OSBUILD_COMMIT}
baseurl=${DNF_REPO_BASEURL}/osbuild/${DISTRO_VERSION}/${ARCH}/${OSBUILD_COMMIT}
enabled=1
gpgcheck=0
# Default dnf repo priority is 99. Lower number means higher priority.
priority=5
EOF

# Install packages needed to generate the test manifests
sudo dnf -y install \
  osbuild \
  osbuild-depsolve-dnf \
  osbuild-luks2 \
  osbuild-lvm2 \
  osbuild-ostree \
  python3
