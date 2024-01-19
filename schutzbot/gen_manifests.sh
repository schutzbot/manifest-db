#!/bin/bash
set -euxo pipefail

git clone https://github.com/osbuild/images.git
cd images
echo "Installing build dependencies"
sudo dnf install -y redhat-rpm-config btrfs-progs-devel device-mapper-devel
sudo dnf build-dep -y osbuild-composer
echo "Generating manifests"
go run ./cmd/gen-manifests -workers 50 -output ../manifests
