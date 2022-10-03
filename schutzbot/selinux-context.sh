set -euxo pipefail
OSBUILD_LABEL=$(matchpathcon -n /usr/bin/osbuild)
chcon $OSBUILD_LABEL tools/image-info
sudo chcon $OSBUILD_LABEL /usr/local/bin/image-info
