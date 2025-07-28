import pathlib

from setuptools import setup

readme_file = pathlib.Path(__file__).parent / "README.md"
long_description = readme_file.read_text()

setup(
    name="safelib",
    version="0.5.0",
    description="A library for safe imports and scoped imports management.",
    author="Mert Sirakaya",
    packages=["safelib"],
    python_requires=">=3.10",
    install_requires=[],
    long_description=long_description,
    maintainer="fswair",
    maintainer_email="contact@tomris.dev",
    long_description_content_type="text/markdown",
    url="https://github.com/fswair/safelib",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
