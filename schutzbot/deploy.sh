#!/bin/bash
set -euxo pipefail


# set locale to en_US.UTF-8
sudo dnf install -y glibc-langpack-en git
localectl set-locale LANG=en_US.UTF-8

# Colorful output.
function greenprint {
    echo -e "\033[1;32m[$(date -Isecond)] ${1}\033[0m"
}

# clone the latest osbuild

git clone https://github.com/osbuild/osbuild.git

# install the latest osbuild

cd osbuild
make rpm
sudo dnf install ./rpmbuild/RPMS/noarch/*.rpm  -y


greenprint "OSBuild installed"
