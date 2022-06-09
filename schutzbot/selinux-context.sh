OSBUILD_LABEL=$(matchpathcon -n $(which osbuild))
chcon $OSBUILD_LABEL tools/image-info
chcon $OSBUILD_LABEL tools/osbuild-image-test
