Mail2Beyond
=========

[![PyLint](https://github.com/jaredhendrickson13/mail2beyond/actions/workflows/pylint.yml/badge.svg)](https://github.com/jaredhendrickson13/mail2beyond/actions/workflows/pylint.yml)
[![Unit Tests](https://github.com/jaredhendrickson13/mail2beyond/actions/workflows/unittest.yml/badge.svg)](https://github.com/jaredhendrickson13/mail2beyond/actions/workflows/unittest.yml/badge.svg)

Mail2Beyond is a Python-based SMTP server designed to redirect incoming SMTP messages to upstream APIs such as
Google Chat, Slack, or even your own API! This includes a command line interface (CLI) that can be used to run
Mail2Beyond as a standalone server, as well as a Python package that you can use to extend or integrate into your own
applications. 

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

## Getting Started
There are a few terms you should be familiar with:

### Listeners
Listeners are individual instances of the Mail2Beyond SMTP server. Listeners define what address, port and protocol the 
server will listen on. Commonly, users will configure a listener for SMTP and another for SMTPS. Additionally, 
listeners can be configured to advertise or require the STARTTLS option to upgrade unencrypted connections to encrypted
connections.

### Connectors
Connectors are simply the API connectors Mail2Beyond can interact with. Built-in connectors include:
- `google_chat` : Sends the incoming SMTP message to Google Chat.
- `slack`       : Sends the incoming SMTP message to Slack
- `smtp`        : Forwards the incoming SMTP message to an upstream SMTP server.
- `void`        : Discards the incoming SMTP message.

### Mappings
Mappings define which SMTP messages use which connector. This checks if a specific SMTP header matches a particular
regular expression. If a match is found, the message is sent using the connector specified in the mapping.

## Developer Documentation
- [CLI Documentation](https://github.com/jaredhendrickson13/mail2beyond/blob/documentation/docs/CLI.md)
- [Python Package Documentation](https://github.com/jaredhendrickson13/mail2beyond/blob/documentation/docs/PACKAGE.md)