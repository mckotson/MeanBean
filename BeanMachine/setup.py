# Packaging the BeanMachine directory

from setuptools import setup
setup(name="BeanMachine",
        version="0.1",
        install_requires = ["gym", "numpy", "numba"])