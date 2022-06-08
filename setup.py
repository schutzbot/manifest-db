import setuptools

setuptools.setup(
    name="image-info",
    description="Tooling for image infos",
    packages=["image-info"],
    license='Apache-2.0',
    entry_points={
        "console_scripts": [
            "image-info = tools.image-info",
            "import-image-tests = tools.import-image-tests",
            "osbuild-image-test = tools.osbuild-image-test",
        ]
    }
)
