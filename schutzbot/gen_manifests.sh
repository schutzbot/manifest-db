#!/bin/bash
set -euxo pipefail

git clone https://github.com/osbuild/images.git
cd images
echo "Installing build dependencies"
sudo ./test/scripts/install-dependencies
echo "Generating manifests"
go run ./cmd/gen-manifests -workers 50 -output ../manifests --cache /var/tmp/rpmmd
