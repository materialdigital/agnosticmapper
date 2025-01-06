from setuptools import setup, find_packages

setup(
    name='agnosticmapper',
    version='1.0',
    install_requires=["rdflib>=7.0.0", "owlready2"],
    packages=find_packages()
)