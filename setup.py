"""Setup file for development installation."""

from setuptools import setup, find_namespace_packages

setup(
    name="alleycat",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
) 