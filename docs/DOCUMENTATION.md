## Getting Started
The following sections provides a basic introduction to using Mail2Beyond as a Python package. You can also use 
Mail2Beyond entirely from the CLI as a standalone server:

[CLI Documentation](#command-line-interface-cli)

### Defining Connector Objects
Connectors are the component that redirects SMTP messages to a specific API or service. There are a handful of built-in
connectors that you can use out of the box, or you can 
[write your own custom connector modules](#writing-custom-connectors). Below is an example of defining connector objects
that redirect SMTP messages to Slack and Google Chat:

```python
import mail2beyond

# Use bulit-in connector modules to create connector objects
void_connector = mail2beyond.connectors.void.Connector()
google_chat_connector = mail2beyond.connectors.google_chat.Connector(
    webhook_url="<YOUR GOOGLE CHAT WEBHOOK URL>"
)
slack_connector = mail2beyond.connectors.google_chat.Connector(
    webhook_url="<YOUR SLACK WEBHOOK URL>"
)
```

### Defining Parser Classes
Parsers allow you to control how the SMTP message's content body is represented before being redirected using a
connector. If you've used the Mail2Beyond CLI, you are likely aware that the CLI's default parser is the auto parser 
that can dynamically choose the best parser based on the SMTP message's content-type header. The Python package requires
the parser class to be specified explicitly, otherwise the BaseParser class is assumed which may have undesired results
as it will leave the content body untouched. Parsers are often used to convert content which is not easily understood
by a human (e.g. HTML content) to a more human-readable format such as markdown. You can reference built-in parser
classes or you can [write your own custom parser classes](#writing-custom-parsers). Parser classes must be defined 
before mappings are defined. Below is an example of defining various parser classes that can be used in your mappings:

```python
import mail2beyond

# Use bulit-in connector modules to create connector objects
void_connector = mail2beyond.connectors.void.Connector()
google_chat_connector = mail2beyond.connectors.google_chat.Connector(
    webhook_url="<YOUR GOOGLE CHAT WEBHOOK URL>"
)
slack_connector = mail2beyond.connectors.google_chat.Connector(
    webhook_url="<YOUR SLACK WEBHOOK URL>"
)

# Reference parser classes to use
auto_parser = mail2beyond.parsers.auto.Parser
html_parser = mail2beyond.parsers.html.Parser
plain_parser = mail2beyond.parsers.plain.Parser
```

#### Notes
- Some connector modules will not respect the parser (e.g. `void`, `smtp`).
- Even when a parser converts the content to a markdown format (e.g. `html`), it does not guarentee the markdown can be
rendered by the service the connector interacts with

### Defining Mapping Objects
Mappings allow you to apply logic to which connectors are used based on the SMTP headers of incoming SMTP messages. A 
specified header is checked for a specific pattern using regular expressions. If a match is found, the connector 
specified in the mapping will be used to redirect the message. Mappings are checked in descending order and are used on 
a first-match basis. At least one mapping must be defined, and at least one mapping must use the pattern `default` to 
assume a default if no other mappings were matched. Connectors must be defined before defining mappings, and mappings 
must be defined before defining listeners. Below is an example of defining various mappings:

```python
import mail2beyond

# Use bulit-in connector modules to create connector objects
void_connector = mail2beyond.connectors.void.Connector()
google_chat_connector = mail2beyond.connectors.google_chat.Connector(
    webhook_url="<YOUR GOOGLE CHAT WEBHOOK URL>"
)
slack_connector = mail2beyond.connectors.google_chat.Connector(
    webhook_url="<YOUR SLACK WEBHOOK URL>"
)

# Reference built-in parser classes to use
auto_parser = mail2beyond.parsers.auto.Parser
html_parser = mail2beyond.parsers.html.Parser
plain_parser = mail2beyond.parsers.plain.Parser

# Define mapping to redirect mail sent to 'google_chat@example.com' to Google Chat
google_chat_mapping = mail2beyond.framework.Mapping(
    pattern="^google_chat@example.com$", 
    field="to",
    connector=google_chat_connector,
    parser=auto_parser
)

# Define mapping that redirects mail from 'slack@example.com' to Slack
slack_mapping = mail2beyond.framework.Mapping(
    pattern="^slack@example.com$", 
    field="from",
    connector=google_chat_connector,
    parser=plain_parser
)

# Define default mapping to discard mail if it did not match another mapping
default_mapping = mail2beyond.framework.Mapping(
    pattern="default", 
    connector=void_connector
)
```

### Defining Listener Objects
Listeners are individual instances of the Mail2Beyond SMTP server. Listeners define what address, port and protocol the 
server will listen on. Commonly, users will configure a listener for SMTP and another for SMTPS. Additionally, 
listeners can be configured to advertise or require the STARTTLS option to upgrade unencrypted connections to encrypted
connections. SMTPS and STARTTLS are configured by creating an `SSLContext` object via Python's `ssl` package. Below is 
an example of defining various listeners:

```python
import mail2beyond
import ssl
import logging

# Use bulit-in connector modules to create connector objects
void_connector = mail2beyond.connectors.void.Connector()
google_chat_connector = mail2beyond.connectors.google_chat.Connector(
    webhook_url="<YOUR GOOGLE CHAT WEBHOOK URL>"
)
slack_connector = mail2beyond.connectors.google_chat.Connector(
    webhook_url="<YOUR SLACK WEBHOOK URL>"
)

# Reference built-in parser classes to use
auto_parser = mail2beyond.parsers.auto.Parser
html_parser = mail2beyond.parsers.html.Parser
plain_parser = mail2beyond.parsers.plain.Parser

# Define mapping to redirect mail sent to 'google_chat@example.com' to Google Chat
google_chat_mapping = mail2beyond.framework.Mapping(
    pattern="^google_chat@example.com$", 
    field="to",
    connector=google_chat_connector,
    parser=auto_parser
)

# Define mapping that redirects mail from 'slack@example.com' to Slack
slack_mapping = mail2beyond.framework.Mapping(
    pattern="^slack@example.com$", 
    field="from",
    connector=google_chat_connector,
    parser=plain_parser
)

# Define default mapping to discard mail if it did not match another mapping
default_mapping = mail2beyond.framework.Mapping(
    pattern="default", 
    connector=void_connector
)  

# Define a normal SMTP listener
smtp_listener = mail2beyond.framework.Listener(
    mappings=[google_chat_mapping, slack_mapping, default_mapping],
    address="localhost",
    port=25,
    log_level=logging.DEBUG
)

# Define an SSLContext for an SMTPS listener
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.set_ciphers("HIGH")
context.minimum_version = ssl.TLSVersion.TLSv1_2
context.load_cert_chain(
    # Change to your actual cert and key
    "/path/to/my/certificate.pem", "/path/to/my/private_key.pem"
)  

# Define an SMTPS listener
smtps_listener = mail2beyond.framework.Listener(
    mappings=[google_chat_mapping, slack_mapping, default_mapping],
    address="localhost",
    port=465,
    tls_context=context,
    log_level=logging.DEBUG
)

# Start each listener and await incoming SMTP messages
smtp_listener.start()
smtps_listener.start()
mail2beyond.framework.Listener.wait()
```

From here, you can simply run your script and Mail2Beyond will be listening for SMTP requests! To verify your setup is
working, you can run the following code in another Python script while the `mail2beyond.framework.Listener` is still
listening:

```python
import smtplib

smtp = smtplib.SMTP("localhost", 25, timeout=10)
smtp.sendmail(
    "slack@example.com",
    "somerecipient@example.com",
    "FROM: slack@example.com\n"
    "TO: somerecipient@example.com\n"
    "Subject: Test subject\n\n"
    "Test body"
)

# Close the SMTP connection.
smtp.close()
```

Assuming your Slack webhook URL was configured correctly, this SMTP message should have matched the `slack_mapping` and
redirected the SMTP message to your Slack channel!

---

## Writing Custom Connectors
The Mail2Beyond framework makes it easy to write your own API connectors to allow you to connect to your own APIs, or 
virtually do anything you'd like with the received SMTP messages!

### Creating the Connector Class
The Mail2Beyond framework includes the `mail2beyond.framework.BaseConnector` class that includes all the necessary 
functions to make your custom connector plug and play. To get started, simply create a `Connector` class that extends 
the `mail2beyond.framework.BaseConnector` class and assign it a default name:

```python
import mail2beyond

class Connector(mail2beyond.framework.BaseConnector):
    name = "my_custom_connnector"
```

### Overwrite the `pre_submit()` Method
The `mail2beyond.framework.BaseConnector.pre_submit()` method is used to validate the Connector object before any 
upstream connection is made. Normally, this method is used to validate the connector object's configuration before 
running the connector. When the object is first created, any keyword arguments (kwargs) passed into the object creation
will be available in the object's `config` attribute. You can overwrite the
`mail2beyond.framework.BaseConnector.pre_submit()` method to ensure required configuration values are present and 
valid. Additionally, the `parser` object is passed to this method and contains the mail headers and content of the SMTP
messsage that triggered the connector and the `log` attribute contains the logger 
you can use to log events that occur within the connector:

```python
import mail2beyond

class Connector(mail2beyond.framework.BaseConnector):
    name = "my_custom_connnector"

    def pre_submit(self, parser):
        self.log.info("starting 'my_custom_connector's pre_submit()!")
        
        # Check that the required 'url' attribute is present
        if "url" not in self.config:
            self.log.error("'url' is required!")
            raise mail2beyond.framework.Error("'url' is required!")
```

### Overwrite the `submit()` Method
The `mail2beyond.framework.BaseConnector.submit()` method is used to perform the main action for this connector. In 
most cases, this will be an API request to an upstream service. A `parser` object is passed to this method that contents
the mail headers and content that triggered this connector and the `log` attribute contains the logger you can use to 
log events that occur within the Connector. Additionally, the `config` attribute will contain any configuration 
required to perform the desired action. Ideally, this `config` attribute will have been fully validated by the 
`mail2beyond.framework.BaseConnector.pre_submit()` method.

```python
import mail2beyond
import requests

class Connector(mail2beyond.framework.BaseConnector):
    name = "my_custom_connnector"

    def pre_submit(self, parser):
        self.log.info("starting 'my_custom_connector's pre_submit()!")
        
        # Check that the required 'url' attribute is present
        if "url" not in self.config:
            self.log.error("'url' is required!")
            raise mail2beyond.framework.Error("'url' is required!")
    
    
    def submit(self, parser):
        # Log informational event
        self.log.info("starting submit()!")
        
        # Example variables
        subject = parser.subject
        content = parser.content
        date = parser.mail.headers.get("date")
        some_header = parser.mail.headers.get("some_header")
        
        # Make an API request to 'url' value found in the config
        try:
            resp = requests.post(
                url=self.config["url"],
                headers={'Content-Type': 'application/json'},
                json={
                    "msg": f"{subject}\n{content}\n{date}\n{some_header}"
                }
            )
            self.log.debug(
                f"connector responded with {resp.status_code} status {resp.text}"
            )
        except Exception as err:
            self.log.error(f"an error occurred!'{err}'")
            raise mail2beyond.framework.Error(f"an error occurred! '{err}'")
```

### Utilizing Your Custom Connector
Now that you've created your custom connector class, you can simply create an object using your connector class and use
it in your mappings like any other connector!

```python
import mail2beyond
import requests
import logging


class Connector(mail2beyond.framework.BaseConnector):
    name = "my_custom_connnector"

    def pre_submit(self, parser):
        self.log.info("starting 'my_custom_connector's pre_submit()!")
        
        # Check that the required 'url' attribute is present
        if "url" not in self.config:
            self.log.error("'url' is required!")
            raise mail2beyond.framework.Error("'url' is required!")
    
    
    def submit(self, parser):
        # Log informational event
        self.log.info("starting submit()!")
        
        # Example variables
        subject = parser.subject
        content = parser.content
        date = parser.mail.headers.get("date")
        some_header = parser.mail.headers.get("some_header")
        
        # Make an API request to 'url' value found in the config
        try:
            resp = requests.post(
                url=self.config["url"],
                headers={'Content-Type': 'application/json'},
                json={
                    "msg": f"{subject}\n{content}\n{date}\n{some_header}"
                }
            )
            self.log.debug(
                f"connector responded with {resp.status_code} status {resp.text}"
            )
        except Exception as err:
            self.log.error(f"an error occurred!'{err}'")
            raise mail2beyond.framework.Error(f"an error occurred! '{err}'")
        
# Create a connector object using your custom connector class
custom_connector = Connector(url="http://myapi.example.com")

# Create a default mapping that uses your custom connector
default_mapping = mail2beyond.framework.Mapping(
    pattern="default", 
    connector=custom_connector
)

# Create and listener that uses the mapping referencing your custom connector
smtp_listener = mail2beyond.framework.Listener(
    mappings=[default_mapping],
    address="localhost",
    port=25,
    log_level=logging.DEBUG
)

# Start the listener
smtp_listener.start()
mail2beyond.framework.Listener.wait()
```

Now you have a `Listener` that will redirect SMTP messages to your API using a custom connector!

## Writing Custom Parsers
In some cases, you may need the SMTP message's content body to be parsed into a very specific format. Luckily the 
Mail2Beyond framework makes this super simple to do. Custom parser classes can be written to allow you to parse the 
content body however you'd like!

### Creating the Parser Class
The Mail2Beyond framework includes the BaseParser class that includes all the functions necessary to make your
custom parser plug and play. To get started, simply create a `Parser` class that extends the 
`mail2beyond.framework.BaseParser` class and assign it a default name:

```python
import mail2beyond

class Parser(mail2beyond.framework.BaseParser):
    name = "my_custom_parser"
```

### Overwrite the `parse_content()` Method
The `mail2beyond.framework.BaseParser.parse_content()` method is used to perform additional formatting to the SMTP 
message's content body. The parser's `mail.content` attribute contains the content body from the received SMTP message. 
In the case the content was sent with an encoding like Base64, the content will _already be decoded_ at this stage. The 
`mail2beyond.framework.BaseParser.parse_content()` can be overwritten to further parse/filter the content before it is
handed to a connector:

```python
import mail2beyond

class Parser(mail2beyond.framework.BaseParser):
    name = "my_custom_parser"

    def parse_content(self):
        # Capture the message's content.
        content = self.mail.content
        
        # Only include content after a specific keyword
        content = content.split("<SOME KEYWORD>")[1]
        
        # Mask sensitive content
        content = content.replace("<SOME SENSITIVE CONTENT>", "*****")
        
        # Return the parsed content
        return content
        
```

### Utilizing Your Custom Parser
Now that you've created your custom parser class, you can simply specify your custom Parser class in your mappings
like any other parser class!

```python
import mail2beyond
import logging

class Parser(mail2beyond.framework.BaseParser):
    name = "my_custom_parser"

    def parse_content(self):
        # Capture the message's content.
        content = self.mail.content
        
        # Only include content after a specific keyword
        content = content.split("<SOME KEYWORD>")[1]
        
        # Mask sensitive content
        content = content.replace("<SOME SENSITIVE CONTENT>", "*****")
        
        # Return the parsed content
        return content

# Create a connector object using your custom connector class
void_connector = mail2beyond.connectors.void.Connector()

# Create a default mapping that uses your custom connector
default_mapping = mail2beyond.framework.Mapping(
    pattern="default", 
    connector=void_connector, 
    parser=Parser
)

# Create a listener that uses the mapping referencing your custom parser
smtp_listener = mail2beyond.framework.Listener(
    mappings=[default_mapping],
    address="localhost",
    port=25,
    log_level=logging.DEBUG
)

# Start the listener
smtp_listener.start()
mail2beyond.framework.Listener.wait()
```

Now you have a `mail2beyond.framework.Listener` that will parse the mail content using your custom parser before 
calling a connector!

# Command Line Interface (CLI)
-----
Mail2Beyond can be used entirely by CLI. After installing Mail2Beyond, you will have access to the ```mail2beyond```
command line tool. The CLI allows you define listeners, connectors and mappings using a JSON or YAML formatted 
configuration file.

## Arguments

| Argument               | Required | Description                                                        |
|------------------------|:---------|--------------------------------------------------------------------|
| `--config (-c) <FILE>` | Yes      | Specifies a config file to load. This must be a JSON or YAML file. |
| `--version (-V)`       | No       | Prints the version of mail2beyond installed.                       |
| `--verbose (-v)`       | No       | Enables verbose logging.                                           |
| `--help (-h)`          | No       | Prints the help page.                                              |

## Configuration
A configuration file must be written before ```mail2beyond``` is started. It may also be helpful to check out the 
[examples on GitHub](https://github.com/soluna-studios/mail2beyond/tree/master/examples/configs). Configuration 
requirements and options are:

-----------------------------------------------------------------------------------------------------------------------
### ```listeners```
A list of listeners for mail2beyond to use. At least one listener must be configured. Each listener has the following 
options available:

**address**

- _Required_: Yes
- _Description_: The IP address this listener will listen on. This must be an address known to the local system.

**port**

- _Required_: Yes
- _Description_: The TCP port this listen will listen on. This must be a numeric value within 1-65535.

**enable_smtps**

- _Required_: No
- _Options_: [`true`, `false`]
- _Default_: false
- _Description_: Enables or disables SMTPS. If set to `true`, the `tls_cert` and `tls_key` options must be set. This
option cannot be set to `true` if `enable_starttls` is also set to `true`.

**enable_starttls**

- _Required_: No
- _Options_: [`true`, `false`]
- _Default_: false
- _Description_: Enables or disables advertisement for the SMTP protocol's STARTTLS function. STARTTLS allows an 
insecure SMTP connections to upgrade to a secure connection. If set to `true`, the `tls_cert` and `tls_key` options 
must be set. This option cannot be set to `true` if `enable_smtps` is also set to `true`.

**require_starttls**

- _Required_: No
- _Options_: [`true`, `false`]
- _Default_: false
- _Description_: Enables or disables requirement for SMTP clients to use the STARTTLS function. If set to `true`, any 
SMTP connection received must use the STARTTLS function to be accepted. This option is only available when 
`enable_starttls` is set to `true`. 

**tls_cert**

- _Required_: Yes w/`enable_smtps` or `enable_starttls`
- _Description_: The file path to the TLS certificate to use for secure connections. Only PEM formatted certificates
are supported. This option is only available when `enable_starttls` is set to `true`. 
  
**tls_key**

- _Required_: Yes w/`enable_smtps` or `enable_starttls`
- _Description_: The file path to the TLS private key to use for secure connections. Only PEM formatted private keys
are supported. This option is only available when `enable_starttls` is set to `true`. 

**minimum_tls_protocol**

- _Required_: No
- _Options_: [`tls1`, `tls1_1`, `tls1_2`, `tls1_3`]
- _Default_: `tls1_2`
- _Description_: Explicitly sets the minimum TLS protocol allowed by the server. Deprecated SSLv2 and SSLv3 are not 
supported as these protocols contain major security vulnerabilities. This option is only available when 
`enable_smtps` or `enable_starttls` is set to `true`. 

### ```connectors```
A list of connectors for mail2beyond to enable. At least one connector item must be configured. Each connector has the 
following options available:

**name**

- _Required_: Yes
- _Description_: The name to assign this connector. This name must be unique from any other connector defined in your 
configuration. This name will be used to assign this connector to mappings in your configuration.

**module**

- _Required_: Yes
- _Options_: [`void`, `smtp`, `google_chat`, `slack`]
- _Description_: The module this connector will use. Multiple connectors can use the same underlying module.

**config**

- _Required_: Dependent on `module` selected.
- _Description_: Additional module specific configurations. Refer to the 
[connector-specific configurations section](#connector-specific-configuration) for requirements and options for the 
specified module for this connector.

### ```mappings```
A list of mapping rules to apply. Mappings allow you to apply logic to which connectors are used based on the SMTP 
headers of incoming SMTP messages. A specified header is checked for a specific pattern using regular expressions. If a
match is found, the connector specified in the mapping will be used to redirect the message. Mappings are checked in 
descending order and are used on a first-match basis. At least one mapping must be defined, and one mapping
must use the pattern `default` to assume a default if no other mappings were matched. Each mapping has the following 
options available:

**pattern**

- _Required_: Yes
- _Description_: The regex pattern to use when checking for matches. 

**connector**

- _Required_: Yes
- _Description_: The name of the connector use upon match. This must be the name of a connector defined in your
configuration. Multiple mappings can use the same the connector.

**parser**

- _Required_: No
- _Options_: [`auto`, `plain`, `html`]
- _Default_: `auto`
- _Description_: Explicitly set the content-type parser to use. By default, the `auto` parser will be chosen to 
select the parser that best matches the SMTP message's content-type header. The `plain` parser will not parse the
content body and is the fallback for the `auto` parser if no parser exists for the content-type. The `html` parser
will parse the content body as HTML and convert it to a more human-readable markdown format.
- _Notes_:
  - Some connector modules do not respect the `parser` option (e.g. `smtp`, `void`)
  - Even though the `html` parser converts the content to markdown, this does not guarantee the markdown content will
  be rendered by the upstream server (e.g. `google_chat`, `slack`)

**field**

- _Required_: No
- _Default_: `from`
- _Description_: The SMTP header to check for a match. Most commonly this will be `from` or `to` to match
based on the sender or recipient of the SMTP message respectively.

## Connector-Specific Configuration
Connector modules may contain their own configurable options and requirements. Below are the available configuration
options available to each built-in connector module:

### ```void```
The `void` connector module simply discards the received SMTP message. This connector module has no available 
configuration options. 

### ```smtp```
The `smtp` connector module forwards received SMTP messages to an upstream SMTP server. On its own, Mail2Beyond does not
actually deliver the SMTP message to the recipient's mailbox. This connector module enables that functionality but 
requires an upstream SMTP to deliver the message. Available options for this module are:

**smtp_host**

- _Required_: Yes
- _Description_: The IP address or hostname of the upstream SMTP server to forward messages to.

**smtp_port**

- _Required_: Yes
- _Description_: The TCP port of the upstream SMTP server. This must be a numeric value within 1-65535. In most cases
this is `25` for SMTP and `465` for SMTPS.

**smtp_use_tls**

- _Required_: No
- _Options_: [`true`, `false`]
- _Default_: `false`
- _Description_: Enable or disable forwarding messages to the upstream SMTP server using SMTPS. If `true`, the 
upstream SMTP server must be configured to allow SMTPS connections.

**smtp_use_login**

- _Required_: No
- _Options_: [`true`, `false`]
- _Default_: `false`
- _Description_: Enable or disable SMTP authentication. If the upstream SMTP server requires authentication, this
option should be set to `true`. If set to `true`, the `smtp_login_user` and `smtp_login_password` must be set.

**smtp_login_user**

- _Required_: Yes w/`smtp_use_login`
- _Description_: The username to authenticate with.

**smtp_login_password**

- _Required_: Yes w/`smtp_use_login`
- _Description_: The password to authenticate with.

### ```slack```
The `slack` module allows SMTP messages to be redirected to a Slack channel using a webhook. A webhook must be
created for your channel beforehand. Available options for this module are:

**webhook_url**

- _Required_: Yes
- _Description_: The full Slack webhook URL. For help to create a webhook, refer to 
https://api.slack.com/messaging/webhooks

### ```google_chat```
The `google_chat` module allows SMTP messages to be redirected to a Google Chat space using an app webhook. A webhook 
must be created for your space beforehand. Available options for this module are:

**webhook_url**

- _Required_: Yes
- _Description_: The full Slack webhook URL. For help to create a webhook, refer to 
https://developers.google.com/chat/how-tos/webhooks

## Starting the Server
Once you have your configuration file written, you can start the server by running the following command:
```commandline
mail2beyond --config /path/to/your/config.yml
```
