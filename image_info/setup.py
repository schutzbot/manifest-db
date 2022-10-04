import setuptools

setuptools.setup(
    name="image-info",
    version="0.0.1",
    description="A info extracting tool for OS images",
    packages=["image_info", "image_info.core", "image_info.utils"],
    license='Apache-2.0',
    install_requires=[
        "osbuild",
        "attrs"
    ],
    entry_points={
        "console_scripts": [
            "image-info = image_info.main_cli:inspect"
        ]
    }
)
