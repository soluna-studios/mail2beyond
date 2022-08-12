Mail2Chat Python Package Documentation
======================================
Mail2Chat is built upon a simple framework that allows developers to integrate Mail2Chat into their own applications, 
extend the existing functionality by writing custom connector and parser modules. If you are just getting started, it
is recommended to first familiarize yourself with the 
[Mail2Chat CLI](https://github.com/jaredhendrickson13/mail2chat/blob/documentation/docs/CLI.md) as it is a great way to
learn how the components work.

## Running the Server
If you've used the Mail2Chat CLI, you are likely already familiar with the concept of connectors, mappings, parsers and 
listeners. These components also apply to the Mail2Chat Python package but are handled slightly differently than the
CLI.

### Defining Connector Objects
Connectors are the component that redirects SMTP messages to a specific API or service. There are a handful of built-in
connectors that you can use out of the box, or you can 
[write your own custom connector modules](#writing-custom-connectors). Below is an example of defining connector objects
that redirect SMTP messages to Slack and Google Chat:

```python
import mail2chat

### DEFINE CONNECTORS
# Use the bulit-in slack and google_chat connector modules to create connector objects
google_chat_connector = mail2chat.connectors.google_chat.Connector(webhook_url="<YOUR GOOGLE CHAT WEBHOOK URL>")
slack_connector = mail2chat.connectors.google_chat.Connector(webhook_url="<YOUR SLACK WEBHOOK URL>")
void_connector = mail2chat.connectors.void.Connector()
```

### Defining Parser Classes
Parsers allow you to control how the SMTP message's content body is represented before being redirected using a
connector. If you've used the Mail2Chat CLI, you are likely aware that the CLI's default parser is the auto parser 
that can dynamically choose the best parser based on the SMTP message's content-type header. The Python package requires
the parser class to be specified explicitly, otherwise the BaseParser class is assumed which may have undesired results
as it will leave the content body untouched. Parsers are often used to convert content which is not easily understood
by a human (e.g. HTML content) to a more human-readable format such as markdown. You can reference built-in parser
classes or you can [write your own custom parser classes](#writing-custom-parsers). Parser classes must be defined 
before mappings are defined. Below is an example of defining various parser classes that can be used in your mappings:

```python
import mail2chat

### DEFINE CONNECTORS
# Use the bulit-in connector modules to create various connector objects
google_chat_connector = mail2chat.connectors.google_chat.Connector(webhook_url="<YOUR GOOGLE CHAT WEBHOOK URL>")
slack_connector = mail2chat.connectors.google_chat.Connector(webhook_url="<YOUR GOOGLE CHAT WEBHOOK URL>")
void_connector = mail2chat.connectors.void.Connector()

### DEFINE PARSERS
# Reference the auto parser class. This will attempt to automatically select the parser to use based on the content-type
# of the received SMTP message. For example, the html parser will be chosen if the content type is text/html.
auto_parser = mail2chat.parsers.auto.Parser

# Reference the html parser class. This will explicitly convert HTML content to a markdown representation.
html_parser = mail2chat.parsers.html.Parser

# Reference the plain parser class. This will not apply any conversion or parsing the content body.
plain_parser = mail2chat.parsers.plain.Parser
```

#### Notes
- Some connector modules will not respect the parser (e.g. `void`, `smtp`).
- Even when a parser converts the content to a markdown format (e.g. `html`), it does not guarentee the markdown can be
rendered by the service the connector interacts with
- .
### Defining Mapping Objects
Mappings allow you to apply logic to which connectors are used based on the SMTP headers of incoming SMTP messages. A 
specified header is checked for a specific pattern using regular expressions. If a match is found, the connector 
specified in the mapping will be used to redirect the message. Mappings are checked in descending order and are used on 
a first-match basis. At least one mapping must be defined, and at least one mapping must use the pattern `default` to 
assume a default if no other mappings were matched. Connectors must be defined before defining mappings, and mappings 
must be defined before defining listeners. Below is an example of defining various mappings:

```python
import mail2chat

### DEFINE CONNECTORS
# Use the bulit-in connector modules to create various connector objects
google_chat_connector = mail2chat.connectors.google_chat.Connector(webhook_url="<YOUR GOOGLE CHAT WEBHOOK URL>")
slack_connector = mail2chat.connectors.google_chat.Connector(webhook_url="<YOUR GOOGLE CHAT WEBHOOK URL>")
void_connector = mail2chat.connectors.void.Connector()

### DEFINE PARSERS
# Reference the auto parser class. This will attempt to automatically select the parser to use based on the content-type
# of the received SMTP message. For example, the html parser will be chosen if the content type is text/html.
auto_parser = mail2chat.parsers.auto.Parser

# Reference the html parser class. This will explicitly convert HTML content to a markdown representation.
html_parser = mail2chat.parsers.html.Parser

# Reference the plain parser class. This will not apply any conversion or parsing the content body.
plain_parser = mail2chat.parsers.plain.Parser

### DEFINE MAPPINGS
# Create a mapping that redirects SMTP messages with recipient 'google_chat@example.com' to Google Chat
google_chat_mapping = mail2chat.framework.Mapping(
    pattern="^google_chat@example.com$", 
    field="to",
    connector=google_chat_connector,
    parser=auto_parser
)

# Create a mapping that redirects SMTP messages with sender 'slack@example.com' to Slack
slack_mapping = mail2chat.framework.Mapping(
    pattern="^slack@example.com$", 
    field="from",
    connector=google_chat_connector,
    parser=plain_parser
)

# Create a default mapping that discards the SMTP message if it did not match any other mapping
default_mapping = mail2chat.framework.Mapping(
    pattern="default", 
    connector=void_connector
)
```

### Defining Listener Objects
Listeners are individual instances of the Mail2Chat SMTP server. Listeners define what address, port and protocol the 
server will listen on. Commonly, users will configure a listener for SMTP and another for SMTPS. Additionally, 
listeners can be configured to advertise or require the STARTTLS option to upgrade unencrypted connections to encrypted
connections. SMTPS and STARTTLS are configured by creating an `SSLContext` object via Python's `ssl` package. Below is 
an example of defining various listeners:

```python
import mail2chat
import ssl
import signal
import logging

### DEFINE CONNECTORS
# Use the bulit-in connector modules to create various connector objects
google_chat_connector = mail2chat.connectors.google_chat.Connector(webhook_url="<YOUR GOOGLE CHAT WEBHOOK URL>")
slack_connector = mail2chat.connectors.google_chat.Connector(webhook_url="<YOUR GOOGLE CHAT WEBHOOK URL>")
void_connector = mail2chat.connectors.void.Connector()

### DEFINE PARSERS
# Reference the auto parser class. This will attempt to automatically select the parser to use based on the content-type
# of the received SMTP message. For example, the html parser will be chosen if the content type is text/html.
auto_parser = mail2chat.parsers.auto.Parser

# Reference the html parser class. This will explicitly convert HTML content to a markdown representation.
html_parser = mail2chat.parsers.html.Parser

# Reference the plain parser class. This will not apply any conversion or parsing the content body.
plain_parser = mail2chat.parsers.plain.Parser

### DEFINE MAPPINGS
# Create a mapping that redirects SMTP messages with recipient 'google_chat@example.com' to Google Chat
google_chat_mapping = mail2chat.framework.Mapping(
    pattern="^google_chat@example.com$", 
    field="to",
    connector=google_chat_connector,
    parser=auto_parser
)

# Create a mapping that redirects SMTP messages with sender 'slack@example.com' to Slack
slack_mapping = mail2chat.framework.Mapping(
    pattern="^slack@example.com$", 
    field="from",
    connector=google_chat_connector,
    parser=plain_parser
)

# Create a default mapping that discards the SMTP message if it did not match any other mapping
default_mapping = mail2chat.framework.Mapping(
    pattern="default", 
    connector=void_connector
)

### DEFINE LISTENERS
# Define an SSLContext for SMTPS
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.load_cert_chain("/path/to/my/certificate.pem", "/path/to/my/private_key.pem")    # Change to your actual cert
context.set_ciphers("HIGH")
context.minimum_version = ssl.TLSVersion.TLSv1_2

# Define a normal SMTP listener
smtp_listener = mail2chat.framework.Listener(
    mappings=[google_chat_mapping, slack_mapping, default_mapping],
    address="localhost",
    port=25,
    log_level=logging.DEBUG
)

# Define an SMTPS listener
smtps_listener = mail2chat.framework.Listener(
    mappings=[google_chat_mapping, slack_mapping, default_mapping],
    address="localhost",
    port=465,
    tls_context=context,
    log_level=logging.DEBUG
)

### START LISTENERS
# Start each listener and pause this script while we await incoming SMTP messages
smtp_listener.start()
smtps_listener.start()
signal.pause()

```

From here, you can simply run your script and Mail2Chat will be listening for SMTP requests!

## Writing Custom Connectors
The Mail2Chat framework makes it easy to write your own API connectors to allow you to connect to your own APIs, or 
virtually do anything you'd like with the received SMTP messages!

### Creating the Connector Class
The Mail2Chat framework includes the BaseConnector class that includes all the necessary functions to make your custom
connector plug and play. To get started, simply create a `Connector` class that extends the 
`mail2chat.framework.BaseConnector` class and assign it a default name:

```python
import mail2chat

class Connector(mail2chat.framework.BaseConnector):
    name = "my_custom_connnector"
```

### Overwrite the BaseConnector's pre_submit() Method:
The `pre_submit()` method is used to validate the Connector object before any upstream connection is made. Normally, 
this method is used to validate the connector object's configuration before running the connector. When the object
is first created, any keyword arguments (kwargs) passed into the object creation will be available in the object's
`config` attribute. You can overwrite the `pre_submit()` method to ensure required configuration values are present and 
valid. Additionally, the `parser` object is passed to this method that contains the mail headers and content of the SMTP
messsage that triggered the connector and the `log` attribute contains the logger you can use to log events that occur 
within the Connector:

```python
import mail2chat

class Connector(mail2chat.framework.BaseConnector):
    name = "my_custom_connnector"

    def pre_submit(self, parser):
        self.log.info("starting 'my_custom_connector's pre_submit()!")
        
        # Check that the required 'url' attribute is present
        if "url" not in self.config:
            self.log.error("an error occurred validating 'my_custom_connector's 'url' config value!")
            raise mail2chat.framework.Error("connector 'my_custom_connector' requires config value for 'url'")
    
```

### Overwrite the BaseConnector's submit() Method:
The `submit()` method is used to perform the main action for this connector. In most cases, this will be an API 
request to an upstream service. A `parser` object is passed to this method that contents the mail headers and content
that triggered this connector and the `log` attribute contains the logger you can use to log events that occur 
within the Connector. Additionally, the `config` attribute will contain any configuration required to perform 
the desired action. Ideally, this `config` attribute will have been fully validated by the `pre_submit()` method.

```python
import mail2chat
import requests

class Connector(mail2chat.framework.BaseConnector):
    name = "my_custom_connnector"

    def pre_submit(self, parser):
        # Log informational event
        self.log.info("starting 'my_custom_connector's pre_submit()!")
        
        # Check that the required 'url' attribute is present
        if "url" not in self.config:
            self.log.error("an error occurred validating 'my_custom_connector's 'url' config value!")
            raise mail2chat.framework.Error("connector 'my_custom_connector' requires config value for 'url'")
    
    def submit(self, parser):
        # Log informational event
        self.log.info("starting 'my_custom_connector's submit()!")
        
        # Example variables
        subject = parser.subject
        content = parser.content
        date = parser.mail.headers.get("date")
        some_specific_header = parser.mail.headers.get(
            "some_specific_header", 
            default="Couldn't find header 'some_specific_header'"
        )
        
        # Make an API request to 'url' value found in the config
        try:
            resp = requests.post(
                url=self.config["url"],
                headers={'Content-Type': 'application/json'},
                json={"msg": f"{subject}\n{content}\n{date}\n{some_specific_header}"}
            )
            self.log.debug(f"connector 'my_custom_connector' responded with {resp.status_code} status {resp.text}")
        except Exception as req_err:
            self.log.error(f"connector 'my_custom_connector' failed '{req_err}'")
            raise mail2chat.framework.Error(f"connector 'my_custom_connector' : {req_err}")
        
        
    
```

### Utilizing Your Custom Connector
Now that you've created your custom connector class, you can simply create an object using your connector class and use
it in your mappings like any other connector!

```python
import mail2chat
import requests
import logging
import signal

class Connector(mail2chat.framework.BaseConnector):
    name = "my_custom_connnector"

    def pre_submit(self, parser):
        # Log informational event
        self.log.info("starting 'my_custom_connector's pre_submit()!")
        
        # Check that the required 'url' attribute is present
        if "url" not in self.config:
            self.log.error("an error occurred validating 'my_custom_connector's 'url' config value!")
            raise mail2chat.framework.Error("connector 'my_custom_connector' requires config value for 'url'")
    
    def submit(self, parser):
        # Log informational event
        self.log.info("starting 'my_custom_connector's submit()!")
        
        # Example variables
        subject = parser.subject
        content = parser.content
        date = parser.mail.headers.get("date")
        some_specific_header = parser.mail.headers.get(
            "some_specific_header", 
            "Couldn't find header 'some_specific_header'"
        )
        
        # Make an API request to 'url' value found in the config
        try:
            resp = requests.post(
                url=self.config["url"],
                headers={'Content-Type': 'application/json'},
                json={"msg": f"{subject}\n{content}\n{date}\n{some_specific_header}"}
            )
            self.log.debug(f"connector 'my_custom_connector' responded with {resp.status_code} status {resp.text}")
        except Exception as req_err:
            self.log.error(f"connector 'my_custom_connector' failed '{req_err}'")
            raise mail2chat.framework.Error(f"connector 'my_custom_connector' : {req_err}")

# Create a connector object using your custom connector class
custom_connecter = Connector(url="http://myapi.example.com")

# Create a default mapping that uses your custom connector
default_mapping = mail2chat.framework.Mapping(pattern="default", connector=custom_connecter)

# Create and listener that uses the mapping referencing your custom connector
smtp_listener = mail2chat.framework.Listener(
    mappings=[default_mapping],
    address="localhost",
    port=25,
    log_level=logging.DEBUG
)

# Start the listener
smtp_listener.start()
signal.pause()

```

Now you have a listener that will redirect SMTP messages to your API using a custom connector!

## Writing Custom Parsers
In some cases, you may need the SMTP message's content body to be parsed into a very specific format. Luckily the 
Mail2Chat framework makes this super simple to do. Custom parser classes can be written to allow you to parse the 
content body however you'd like!

### Creating the Parser Class
The Mail2Chat framework includes the BaseParser class that includes all the functions necessary to make your
custom parser plug and play. To get started, simply create a `Parser` class that extends the 
`mail2chat.framework.BaseParser` class and assign it a default name:

```python
import mail2chat

class Parser(mail2chat.framework.BaseParser):
    name = "my_custom_parser"
```

### Overwrite the BaseParser's parse_content() Method:
The `parse_content()` method is used to perform additional formatting to the SMTP message's content body. The parser's
`mail.content` attribute contains the content body from the received SMTP message. In the case the content was sent 
with an encoding like Base64, the content will _already be decoded_ at this stage. The `parse_content()` can be
overwritten to further parse/filter the content before it handed to a connector:

```python
import mail2chat

class Parser(mail2chat.framework.BaseParser):
    name = "my_custom_parser"

    def parse_content(self):
        # Capture the message's content. The self.mail.content cannot be directly modified!
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
import mail2chat
import logging
import signal

class Parser(mail2chat.framework.BaseParser):
    name = "my_custom_parser"

    def parse_content(self):
        # Capture the message's content. The self.mail.content cannot be directly modified!
        content = self.mail.content
        
        # Only include content after a specific keyword
        content = content.split("<SOME KEYWORD>")[1]
        
        # Mask sensitive content
        content = content.replace("<SOME SENSITIVE CONTENT>", "*****")
        
        # Return the parsed content
        return content

# Create a connector object using your custom connector class
void_connector = mail2chat.connectors.void.Connector()

# Create a default mapping that uses your custom connector
default_mapping = mail2chat.framework.Mapping(pattern="default", connector=void_connector, parser=Parser)

# Create and listener that uses the mapping referencing your custom connector
smtp_listener = mail2chat.framework.Listener(
    mappings=[default_mapping],
    address="localhost",
    port=25,
    log_level=logging.DEBUG
)

# Start the listener
smtp_listener.start()
signal.pause()

```

Now you have a listener that will parse the mail content using your custom parser before calling a connector!
