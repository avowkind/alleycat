"""Setup file for development installation."""

from setuptools import find_namespace_packages, setup

setup(
    name="alleycat",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
)
