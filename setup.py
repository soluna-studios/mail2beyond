# Copyright 2022 Jared Hendrickson
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from setuptools import setup


def read_me():
    # Read the readme file
    with open('README.md') as f:
        return f.read()


def requirements():
    with open('requirements.txt') as r:
        # Read the requirements file and split string in list by newline
        reqs = r.read().split("\n")

        # Remove empty items if any
        while "" in reqs:
            reqs.remove("")

        return reqs


setup(
    name='mail2chat',
    author='Jared Hendrickson',
    author_email='jaredhendrickson13@gmail.com',
    url="https://github.com/jaredhendrickson13/pfsense-vshell",
    license="Apache-2.0",
    description="An SMTP server that relays messages to Google Chat.",
    long_description=read_me(),
    long_description_content_type="text/markdown",
    version="1.0.0",
    scripts=['scripts/mail2chat'],
    packages=["mail2chat", "mail2chat.connectors"],
    install_requires=requirements(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6'
)
