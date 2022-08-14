"""Module used to setup and install the mail2beyond package."""

from setuptools import setup


def read_me():
    """Opens the README.md file for this package so it can by used in setup.py."""
    # Read the readme file
    with open('README.md', encoding="utf-8") as read_me_file:
        return read_me_file.read()


def requirements():
    """Opens the requirements.txt file for this package so it can by used in setup.py."""
    with open('requirements.txt', encoding="utf-8") as requirements_file:
        # Read the requirements file and split string in list by newline
        reqs = requirements_file.read().split("\n")

        # Remove empty items if any
        while "" in reqs:
            reqs.remove("")

        return reqs


setup(
    name='mail2beyond',
    author='Jared Hendrickson',
    author_email='jaredhendrickson13@gmail.com',
    url="https://github.com/soluna-studios/mail2beyond",
    license="MIT",
    description="A Python based SMTP server package and CLI that redirects incoming SMTP messages to upstream APIs like"
                " Google Chat, Slack and more!.",
    long_description=read_me(),
    long_description_content_type="text/markdown",
    version="1.0.0",
    scripts=['scripts/mail2beyond'],
    packages=["mail2beyond", "mail2beyond.connectors", "mail2beyond.parsers"],
    install_requires=requirements(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8'
)
