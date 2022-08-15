"""Module used to setup and install the mail2beyond package."""

import os
import codecs

from setuptools import setup


def read(rel_path):
    """Reads a specified file."""
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as filepath:
        return filepath.read()


def get_readme():
    """Opens the README.md file for this package so it can by used in setup.py."""
    # Read the readme file
    return read("README.md")


def get_requirements():
    """Opens the requirements.txt file for this package so it can be used in setup.py."""
    reqs = read("requirements.txt").split("\n")

    # Remove empty items if any
    while "" in reqs:
        reqs.remove("")

    return reqs


def get_version(rel_path):
    """
    Gets the current version of the package. If a __MAIL2BEYOND_REVISION__ environment variable exists, it will
    be read and appended to the current package version. This is used to ensure the setup version can always be unique
    for PyPI dev builds triggered by CI/CD workflows.
    """
    # Variables
    revision = ""

    # If a __MAIL2BEYOND_REVISION__ environment variable exists, set it as the dev revision.
    if "__MAIL2BEYOND_REVISION__" in os.environ:
        revision = "." + os.environ.get("__MAIL2BEYOND_REVISION__")

    # Otherwise, look for the version in the package.
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1] + revision

    raise RuntimeError("Unable to find version string.")


setup(
    name='mail2beyond',
    author='Jared Hendrickson',
    author_email='jaredhendrickson13@gmail.com',
    url="https://github.com/soluna-studios/mail2beyond",
    license="MIT",
    description="A Python based SMTP server package and CLI that redirects incoming SMTP messages to upstream APIs like"
                " Google Chat, Slack and more!.",
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    version=get_version("mail2beyond/__init__.py"),
    scripts=['scripts/mail2beyond'],
    packages=["mail2beyond", "mail2beyond.connectors", "mail2beyond.parsers"],
    install_requires=get_requirements(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8'
)
