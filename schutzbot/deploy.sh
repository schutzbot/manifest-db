#!/bin/bash
set -euxo pipefail

sudo dnf install -y jq


DNF_REPO_BASEURL=http://osbuild-composer-repos.s3.amazonaws.com

# The osbuild-composer commit to run reverse-dependency test against.
# Currently: rpmbuild: build rpms on RHEL 8.8 and 9.2
OSBUILD_COMPOSER_COMMIT=caac5fc7af0ec59df7bcb590de233f82cdcef4e8
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
name=osbuild ${CI_COMMIT_SHA}
baseurl=${DNF_REPO_BASEURL}/osbuild/${DISTRO_VERSION}/${ARCH}/${OSBUILD_COMMIT}
enabled=1
gpgcheck=0
# Default dnf repo priority is 99. Lower number means higher priority.
priority=5

[osbuild-composer]
name=osbuild-composer ${OSBUILD_COMPOSER_COMMIT}
baseurl=${DNF_REPO_BASEURL}/osbuild-composer/${DISTRO_VERSION}/${ARCH}/${OSBUILD_COMPOSER_COMMIT}
enabled=1
gpgcheck=0
# Give this a slightly lower priority, because we used to have osbuild in this repo as well.
priority=10
EOF

if [[ $ID == rhel || $ID == centos ]] && ! rpm -q epel-release; then
    # Set up EPEL repository (for ansible and koji)
    sudo dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-${VERSION_ID%.*}.noarch.rpm
fi

# Install the Image Builder packages.
# Note: installing only -tests to catch missing dependencies
sudo dnf -y install osbuild-composer-tests

# Set up a directory to hold repository overrides.
sudo mkdir -p /etc/osbuild-composer/repositories

# Temp fix until composer gains these dependencies
sudo dnf -y install osbuild-luks2 osbuild-lvm2
