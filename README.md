Mail2Beyond
=========
[![PyPI](https://github.com/soluna-studios/mail2beyond/actions/workflows/pypi.yml/badge.svg)](https://github.com/soluna-studios/mail2beyond/actions/workflows/pypi.yml)
[![Documentation Build](https://github.com/soluna-studios/mail2beyond/actions/workflows/documentation.yml/badge.svg)](https://github.com/soluna-studios/mail2beyond/actions/workflows/documentation.yml)
[![Unit Tests](https://github.com/soluna-studios/mail2beyond/actions/workflows/unittest.yml/badge.svg)](https://github.com/soluna-studios/mail2beyond/actions/workflows/unittest.yml)
[![PyLint](https://github.com/soluna-studios/mail2beyond/actions/workflows/pylint.yml/badge.svg)](https://github.com/soluna-studios/mail2beyond/actions/workflows/pylint.yml)
[![CodeQL](https://github.com/soluna-studios/mail2beyond/actions/workflows/codeql.yml/badge.svg)](https://github.com/soluna-studios/mail2beyond/actions/workflows/codeql.yml)

Mail2Beyond is a Python-based SMTP server designed to redirect incoming SMTP messages to upstream APIs such as
Google Chat, Slack, or even your own API! This includes a command line interface (CLI) that can be used to run
Mail2Beyond as a standalone server, as well as a Python package that you can use to extend or integrate into your own
applications. 

## Installation
To install Mail2Beyond, simply run the following command:
```
pip install mail2beyond
```

## Usage
Before starting the Mail2Beyond server, you must 
[create your configuration file](https://soluna-studios.github.io/mail2beyond/index.html#configuration). Once you have
your configuration file ready, you can start the server by running:
```
mail2beyond --config /path/to/your/config.yml
```

## Developer Documentation
- [API Reference](https://soluna-studios.github.io/mail2beyond/)

## How is This Useful? 
Emails are often ignored due to the amount of spam we receive on a daily basis. Many systems and applications use SMTP
to send mail alerts, notices and other information that may be important. This commonly causes important information to
be overlooked or outright ignored. At the same time, many organizations are using real-time messaging services like
Google Chat and Slack on a daily basis. Mail2Beyond allows you to redirect these important messages to these services
to help keep your teams informed!

Beyond messaging services, Mail2Beyond can also be extended to include connectors to your own APIs to build out complex
automation flows based on incoming SMTP messages.

## How Does Mail2Beyond Work?
Mail2Beyond continually listens for incoming SMTP messages. When a message is received, the message is parsed and checked
against a set of admin configured mappings that dictate which API connector is to be used. Mappings define which SMTP 
headers should be checked for a specific regular expression match. When a match is found, the email contents are parsed
and sent to the upstream API using the connector specified in the mapping.
