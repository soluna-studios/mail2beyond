"""Module that contains the core framework for mail2beyond."""

import email
import inspect
import ipaddress
import re
import logging
import signal
import ssl

from aiosmtpd.controller import Controller


class Error(BaseException):
    """Creates the `Error` object used by mail2beyond."""
    def __init__(self, message: str):
        super().__init__(message)


class Email:
    """
    Creates an `Email` object that contains a decoded SMTP email along with information about the client and server.

    Attributes:
        server (aiosmtpd.smtp.SMTP): The `SMTP` object that handled the email from `aiosmtpd`.
        session (aiosmtpd.smtp.Session): The `Session` object that contains client-connection info from `aiosmtpd`.
        envelope (aiosmtpd.smtp.Envelope): The `Envelope` object that contains the original email as it was received by
            the server from `aiosmtpd`.
        headers (email.message.Message): The Message object from the 'email' Python module that contains the decoded
            SMTP headers.


    """

    def __init__(self, server, session, envelope):
        """
        Initializes the `Email` object with required attributes using parameters.

        Args:
            server (aiosmtpd.smtp.SMTP): The `SMTP` object that handled the email from `aiosmtpd`.
            session (aiosmtpd.smtp.Session): The `Session` object that contains client-connection info from `aiosmtpd`.
            envelope (aiosmtpd.smtp.Envelope): The `Envelope` object that contains the original email as it was received
                by the server from `aiosmtpd`.
        """
        self.server = server
        self.session = session
        self.envelope = envelope
        self.headers = email.message_from_bytes(envelope.content)

    def get_peer_ip(self):
        """Gets the IP of the remote peer (client)."""
        return self.session.peer

    def get_peer_ip_and_port(self):
        """Gets the IP and port of the remote peer (client) in IP:PORT format."""
        return f"{self.session.peer[0]}:{self.session.peer[1]}"

    def get_server_ip_and_port(self):
        """Gets the IP and port of the server that accepted the email in IP:PORT format."""
        return f"{self.server.event_handler.address}:{self.server.event_handler.port}"

    # Getters and setters
    @property
    def content(self):
        """Gets the decoded content body from the email."""
        return self.headers.get_payload(decode=True).decode()


class Listener:
    """
    Creates the `Listener` object that accepts SMTP/SMTPS requests and applies logic based on a specified mappings.

    Attributes:
        log (logging.Logger): The Logger object the `Listener` will use to log events that occur while listening.
        controller (aiosmtpd.controller.Controller): The `Controller` from `aiosmtpd` that controls the SMTP server.
    """
    # Private attributes are not for public consumption.
    # pylint: disable=too-many-instance-attributes

    # Initialize attributes.
    _address = None
    _port = None
    _mappings = None
    _tls_context = None
    _enable_starttls = None
    _require_starttls = None

    def __init__(self, mappings: list, address: str = "127.0.0.1", port: int = 62125, **kwargs):
        """
        Initializes the `Listener` with the required attributes from arguments.

        Args:
            mappings (list): A list of `mail2beyond.framework.Mapping` objects that this listener check whenever an
                SMTP message is received. At list one item is required and one item must be a Mapping with its `pattern`
                attribute set to `default`.
            address (str): The local address the `Listener` will listen for SMTP requests on.
            port (int): The local TCP port the `Listener` will listen for SMTP requests on.
            **tls_context (ssl.SSLContext): The SSLContext object from the 'ssl' library that defines the TLS
                configuration for an SMTPS listener. If `None` is specified, the `Listener` will not use TLS.
            **enable_starttls (bool): Enables or disables allowing advertisement of the STARTTLS option that allows
                clients to automatically upgrade insecure SMTP connections to secure connections. This argument is only
                applicable if you have provided a valid `tls_context`.
            **require_starttls (bool): Enables or disables requiring clients to use the STARTTLS option. If enabled, all
                clients must choose the STARTTLS option or the request will be rejected. This argument is only
                applicable if you have set `enable_starttls` to `True`.
        """
        # Setup logging
        self.log = None
        self.setup_logging(kwargs.get("log_level", logging.NOTSET))

        # Setup mappings and the SMTP controller
        self.controller = None
        self.mappings = mappings
        self.address = address
        self.port = port
        self.tls_context = kwargs.get("tls_context", None)
        self.enable_starttls = kwargs.get("enable_starttls", False)
        self.require_starttls = kwargs.get("require_starttls", False)
        self.setup_controller()

    def start(self):
        """
        Starts the `Listener`. This will run the SMTP server in the background. After calling this method, you will
            need to keep the process alive for the SMTP server to continue receiving SMTP connections. You can call the
        `wait()` method to keep the server running indefinitely, or use a function like time.sleep() to keep the
            SMTP server running for a specified amount of time.
        """
        self.controller.start()
        self.log.info(f"mail2beyond started listening on {self.address}:{self.port}")
        self.log_mappings()

    @staticmethod
    def wait():
        """
        Allows the `Listener` to wait indefinitely, so it can continually accept incoming SMTP messages. This is
        typically called immediately after the `start()` method.
        """
        signal.pause()

    def setup_controller(self):
        """
        Sets up the `Controller` object with the current address, port and options. If you have made changes to your
        `Listener` object, you will need to call this method to reconfigure the `Controller`.

        Raises:
            mail2beyond.framework.Error: When an unexpected error occurs when creating controllers.
        """
        # Setup SMTPS controller if enabled
        if self.tls_context and not self.enable_starttls:
            self.controller = Controller(self, hostname=self.address, port=self.port, ssl_context=self.tls_context)
        # Setup STARTTLS controller if enabled
        elif self.tls_context and self.enable_starttls:
            self.controller = Controller(
                self,
                hostname=self.address,
                port=self.port,
                tls_context=self.tls_context,
                require_starttls=self.require_starttls
            )
        # Setup SMTP controller if no tls_context was provided
        elif not self.tls_context:
            self.controller = Controller(self, hostname=self.address, port=self.port)
        # Throw an error if we somehow ended up here
        else:
            raise Error("an unexpected error occurred creating the Listener controller")

    def setup_logging(self, level: int = logging.NOTSET, handler=None, **kwargs):
        """
        Sets up the `log` attribute with a configurable Logger for this `Listener`.

        Args:
            level (int): Sets the logging level the Logger will start logging at. See
                https://docs.python.org/3/library/logging.html#logging-levels
            handler (logging.Handler): Sets the logging handler to use. You can pass in a custom Handler like a
                logging.FileHandler to log to a file. If no handler is specified, the default handler
                logging.StreamHandler is assumed which will only print logs to the console.
            **log_format (str): Sets the format of log messages. See
                https://docs.python.org/3/library/logging.html#logging.Formatter.format
            **log_date_format (str): Sets the format of datetime strings in log messages. See
                https://docs.python.org/3/library/logging.html#logging.Formatter.formatTime
        """

        # Reset the existing logger
        del self.log

        # Set formatting
        log_format = kwargs.get("log_format", "[%(asctime)s][%(levelname)s]:%(message)s")
        log_date_format = kwargs.get("log_date_format", "%b %d %Y %H:%M:%S")

        # Set handler
        handler = handler if handler else logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=log_date_format))

        # Set the logger
        self.log = logging.getLogger(__name__)
        self.log.setLevel(level)
        self.log.addHandler(handler)

        # Re-assign assigned mappings to re-populate connector loggers
        if self.mappings:
            self.mappings = self.mappings

        # Log debug notice if debug level set
        if level == logging.DEBUG:
            self.log.warning("logging at level DEBUG may expose sensitive information in logs")

    def log_mappings(self):
        """Logs the configured mappings upon startup for debugging."""
        # Loop through all configured mappings and log it's configuration.
        for mapping in self.mappings:
            self.log.debug(
                f"loaded mapping with pattern='{ mapping.pattern }' field='{ mapping.field }'"
                f" connector='{ mapping.connector }' connector_module='{ mapping.connector.__module__ }'"
                f" parser={ mapping.parser }"
            )

    def get_default_mapping(self, mappings: (list, None) = None):
        """
        Gets the mapping with the `default` pattern from a list of mappings.

        Args:
            mappings (list, None): The list of Mapping objects to search. If none are provided, the mappings defined
                in the `mappings` attribute value will be assumed.

        Raises:
            mail2beyond.framework.Error: When no Mapping object within the list has its `pattern` set to `default`.
        """
        # Variables
        mappings = mappings if mappings else self.mappings

        # Loop through each mapping and find the default.
        for mapping in mappings:
            if mapping.pattern == "default":
                return mapping

        # Return nothing if no default was found.
        raise Error("mapping with 'default' pattern is required")

    def get_mapping_matches(self, mail: Email):
        """
        Gets the mappings that match a specific `Email` object.

        Args:
            mail (mail2beyond.framework.Email): The `Email` object to check for Mapping matches.

        Returns
            list: a list of Mapping objects that matched this `Email`.
        """
        # Initialize the default mapping in case there were no direct matches.
        default_mapping = self.get_default_mapping()
        matched_mappings = []

        # Loop through each mapping to check if the condition matches
        for mapping in self.mappings:
            # Only match default as last resort
            if mapping != default_mapping:
                if mapping.is_match(mail.headers.get(mapping.field, None)):
                    matched_mappings.append(mapping)

        # Return the matched mappings if there were any, otherwise return the default mapping.
        if matched_mappings:
            return matched_mappings

        # Otherwise return default mapping
        return [default_mapping]

    async def handle_DATA(self, server, session, envelope):
        """
        Overwrites the `handle_DATA()` method from `aiosmtpd` that defines how received SMTP data is handled. There
        shouldn't be any need for this method to be called explicitly as it is used exclusively by `aiosmtpd`.

        See Also:
            https://aiosmtpd.readthedocs.io/en/latest/handlers.html#handle_DATA

        Args:
            server (aiosmtpd.smtp.SMTP): The `SMTP` object that handled the email from `aiosmtpd`.
            session (aiosmtpd.smtp.Session): The `Session` object that contains client-connection info from `aiosmtpd`.
            envelope (aiosmtpd.smtp.Envelope): The `Envelope` object that contains the original email as it was received
                by the server from `aiosmtpd`.
        """
        # Create an email object with the received session and data
        mail = Email(server, session, envelope)

        # Log this connection
        self.log.info(f"server {mail.get_server_ip_and_port()} connection from peer {mail.get_peer_ip_and_port()}")

        # Pull the mapping that matches this message and send the chat accordingly.
        mappings = self.get_mapping_matches(mail)

        # Loop through each matched mapping and run it's connector
        for mapping in mappings:
            self.log.debug(
                f"running connector '{mapping.connector}' because {mapping.field.upper()} "
                f"'{mail.headers.get(mapping.field)}' matched mapping '{mapping.pattern}'"
            )

            # Run the connector with this mapping's parser
            self.log.debug(f"using parser '{mapping.parser}'")
            mapping.connector.run(mapping.parser(mail))

        return '250 Message accepted'

    # Getters and setters
    @property
    def address(self):
        """The property to get and/or set the  address attribute."""
        return self._address

    @address.setter
    def address(self, value: str):
        """Sets the address attribute after validating the new value."""
        # Require address to be valid IP, or localhost
        if value not in ["localhost"]:
            try:
                ipaddress.ip_address(value)
            except ValueError as exc:
                raise Error("'address' must be valid IP or localhost") from exc

        self._address = value

    @property
    def port(self):
        """The property to get and/or set the  port attribute."""
        return self._port

    @port.setter
    def port(self, value: int):
        """Sets the port attribute after validating the new value."""
        # Require port to be valid TCP port
        if isinstance(value, int) and 1 <= value <= 65535:
            self._port = value
        else:
            raise Error("'port' must be valid TCP port")

    @property
    def mappings(self):
        """The property to get and/or set the  mappings attribute."""
        return self._mappings

    @mappings.setter
    def mappings(self, value: list):
        """Sets the mappings attribute after validating the new value."""
        # Require mappings to be list
        if not isinstance(value, list):
            raise TypeError("'mappings' must be type 'list'")

        # Loop through each requested mapping and it is correct object type and a default object is present
        found_default = False
        for mapping in value:
            # Require mapping to be Mapping object
            if not isinstance(mapping, Mapping):
                raise Error("each 'mappings' item must be 'Mapping' object")

            # Check if this mapping is the default.
            if mapping.pattern == "default":
                # Ensure we have not already found a default
                if not found_default:
                    found_default = True
                else:
                    raise Error("multiple 'mappings' items assigned pattern 'default'")

            # Assign this listener's logger to each mapping connector
            mapping.connector.log = self.log

        # Ensure we found a default mapping
        if found_default:
            self._mappings = value

        else:
            raise Error("missing 'mappings' item with pattern 'default'")

    @property
    def tls_context(self):
        """The property to get and/or set the  tls_context attribute."""
        return self._tls_context

    @tls_context.setter
    def tls_context(self, value: ssl.SSLContext):
        """Sets the tls_context attribute after validating the new value."""
        # Require tls_context to be SSLContext object or None
        if isinstance(value, ssl.SSLContext) or value is None:
            self._tls_context = value
        else:
            raise Error("'tls_context' must be type 'ssl.SSLContext' or 'None'")

    @property
    def enable_starttls(self):
        """The property to get and/or set the  enable_starttls attribute."""
        return self._enable_starttls

    @enable_starttls.setter
    def enable_starttls(self, value: bool):
        """Sets the enable_starttls attribute after validating the new value."""
        # Require enable_starttls to be bool
        if isinstance(value, bool):
            self._enable_starttls = value
        else:
            raise Error("'enable_starttls' must be type 'bool'")

    @property
    def require_starttls(self):
        """The property to get and/or set the  require_starttls attribute."""
        return self._enable_starttls

    @require_starttls.setter
    def require_starttls(self, value: bool):
        """Sets the require_starttls attribute after validating the new value."""
        # Require require_starttls to be bool
        if not isinstance(value, bool):
            raise Error("'require_starttls' must be type 'bool'")

        # Require 'enable_tls' to be True before allowing
        if not self.enable_starttls and value:
            raise Error("'require_starttls' cannot be 'True' while 'enable_starttls' is 'False'")

        self._require_starttls = value


class Mapping:
    """
    Creates a Mapping object that defines parameters to control the formatting and redirection of received SMTP
    messages. Whenever an SMTP message is received, Mappings are checked by the `Listener` to see if the received SMTP
    message headers match the regex defined in the Mapping object.
    """
    # Private attributes are not for public consumption.
    # pylint: disable=too-many-instance-attributes

    # Initialize attributes
    _pattern = None
    _field = None
    _connector = None
    _parser = None

    def __init__(self, pattern: str, connector, **kwargs):
        """
        Initializes the Mapping object with desired attributes.

        Args:
            pattern (str): The regex pattern to use when checking SMTP headers for specific values.
            connector (mail2beyond.framework.BaseConnector): The Connector object this Mapping will use whenever a
                match is found. This must be an object of a class that has a base class of
                `mail2beyond.framework.BaseConnector`. You should pass in a built-in `Connector` object created from the
                mail2beyond.connectors module or your own custom `Connector` object.
            **field (str) The SMTP header to run the regex pattern against. This is commonly the TO or FROM headers to
                check the email's recipient or sender respectively, but can be any header available in the received
                email. Defaults to `from`.
            **parser (mail2beyond.framework.BaseParser): The Parser class to use whenever this Mapping is matched. This
                allows you to specify a Parser class that will parse the email's content body to a more human-readable
                format. Note this must be the Parser class NOT a `Parser` object. This must be Parser class with a base
                class of `mail2beyond.framework.BaseParser`. Defaults to the `mail2beyond.framework.BaseParser` class,
                but it is strongly recommended you pass in `mail2beyond.parsers.auto.Parser` to automatically parse
                the content body based on the email's content-type header or pass in your own custom parser class.

        See Also:
            https://github.com/soluna-studios/mail2beyond/blob/master/docs/PACKAGE.md#writing-custom-connectors
            https://github.com/soluna-studios/mail2beyond/blob/master/docs/PACKAGE.md#writing-custom-parsers
        """
        # Assign required attributes
        self.pattern = pattern
        self.connector = connector

        # Assign optional attributes, or assume defaults.
        self.field = kwargs.get("field", "from")
        self.parser = kwargs.get("parser", BaseParser)

    def __str__(self):
        """Sets the object's pattern as the string representation of this object."""
        return self.pattern

    def is_match(self, value):
        """
        Checks if a specified value matches this mapping.

        Args:
            value (str): The value to check for a regex pattern match.

        Returns:
            bool: Whether the value was a match for the regex pattern or not.
        """
        # Check if the value matches this mapping's regex pattern.
        if value is not None and re.search(self.pattern, value):
            return True
        # No match, return False
        return False

    # Getters and setters #
    @property
    def pattern(self):
        """The property to get and/or set the  pattern attribute."""
        return self._pattern

    @pattern.setter
    def pattern(self, value: str):
        """Sets the pattern attribute after validating the new value."""
        # Require pattern to be a string
        if isinstance(value, str):
            self._pattern = value
        else:
            raise TypeError("pattern must be type 'str'")

    @property
    def connector(self):
        """The property to get and/or set the  connector attribute."""
        return self._connector

    @connector.setter
    def connector(self, value):
        """Sets the connector attribute after validating the new value."""
        # Require connector to have a base class of mail2beyond.framework.BaseConnector
        if value.__class__.__base__ == BaseConnector:
            self._connector = value
        else:
            raise TypeError("connector must be object with base class 'BaseConnector'")

    @property
    def parser(self):
        """The property to get and/or set the  parser attribute."""
        return self._parser

    @parser.setter
    def parser(self, value):
        """Sets the parser attribute after validating the new value."""
        # Require parser to have a base class of mail2beyond.framework.BaseParser
        if inspect.isclass(value) and issubclass(value, BaseParser):
            self._parser = value
        else:
            raise TypeError("parser must be a class (not object) with base class 'BaseParser'")

    @property
    def field(self):
        """The property to get and/or set the  field attribute."""
        return self._field

    @field.setter
    def field(self, value: str):
        """Sets the field attribute after validating the new value."""
        # Require field to be a support/recognized field
        if isinstance(value, str):
            self._field = value
        else:
            raise ValueError("field must be type 'str'")


class BaseConnector:
    """
    Creates the BaseConnector object to be extended by configurable child classes. This establishes standard
    methods and attributes for creating plugin API connectors.

    Attributes:
        name (str): The name of the created object. This attribute is primarily used for the CLI, but could be useful
            for other reasons.
        log (logging.Logger): The Logger object to use when logging events that occur when the `Connector` is called.
        config (dict): The dict of custom `Connector` configuration values. Any arguments passed in when the object
            is initially created will be populated here. Some Connectors will require configurable values like URLs,
            credentials, etc. This is where those values should be passed in.
    """
    # Attributes
    name = ""

    def __init__(self, **kwargs):
        """
        Initialize the object with required attributes.

        Notes:
            Any arguments passed in when this object is created will be stored in the 'config' attribute of the object.
        """
        self.config = kwargs
        self.log = logging.getLogger(__name__)

    def __str__(self):
        """Sets this object's name attribute as its string representation."""
        return self.name

    def run(self, parser):
        """
        Runs the current connector object. This method calls the `pre_submit()` and `submit()` methods respectively and
        checks for any errors encountered.

        Args:
            parser (mail2beyond.framework.BaseParser): The `Parser` object to use when this `Connector` is called. This
                will the object created by the mapping's parser and will contain the parsed email content.
                Note this must be the `Parser` object NOT a `Parser` class. This must be `Parser` object with a base
                class of `mail2beyond.framework.BaseParser`.

        Raises:
            mail2beyond.framework.Error: When the `pre_submit()` method catches a `mail2beyond.framework.Error`.
            Exception: When the `submit()` method catches any error, the error will simply be re-raised by this method.
        """
        # Try to run pre-submit checks and log errors.
        try:
            self.pre_submit(parser)
        except Error as pre_submit_err:
            self.log.error(f"pre-submit checks for connector '{self}' failed ({pre_submit_err})")
            raise pre_submit_err

        # Try to run a submit and log errors
        try:
            self.submit(parser)
        except Exception as submit_error:
            self.log.error(f"submit for connector '{self}' failed ({submit_error})")
            raise submit_error

    def submit(self, parser):
        """
        Initializes the `submit()` method that performs actions required for the connector redirect the SMTP message.
        This method is intended to be overwritten by a child class that creates a `Connector` object for a specific API
        or service. If this method is not overwritten by the child class, an error is raised. When overwriting this
        method, you can use the `parser` object to reference various components in the received SMTP message and the
        `config` attribute to reference required configuration values. You can also log events in this method using
        the `log` attribute.

        Args:
            parser (mail2beyond.framework.BaseParser): The `Parser` object to use when this `Connector` is called. This
                will the object created by the mapping's parser and will contain the parsed email content.
                Note this must be the `Parser` object NOT a `Parser` class. This must be `Parser` object with a base
                class of `mail2beyond.framework.BaseParser`.

        Raises:
            mail2beyond.framework.Error: When the `submit()` method has not been overwritten by a child class.
        """
        raise Error(f"method has not been overwritten by child class but received {parser}")

    def pre_submit(self, parser):
        """
        Initializes the `pre_submit()` method that performs validation before the connector's `submit()` method is
        called.This method is intended to be overwritten by a child class that creates `Connector` objects for a
        specific API. Typically, ths method will be used to validate the contents of the `Connector` object's `config`
        attribute. But could also be used to validate the parsed email values using the `parser` attribute. When
        overwriting this method, simply raise a `mail2beyond.framework.Error` to mark the `pre_submit()` checks as a
        failure. You can also log events in this method using the `log` attribute.

        Args:
            parser (mail2beyond.framework.BaseParser): The `Parser` object to use when this `Connector` is called. This
                will the object created by the mapping's parser and will contain the parsed email content.
                Note this must be the `Parser` object NOT a `Parser` class. This must be `Parser` object with a base
                class of `mail2beyond.framework.BaseParser`.

        Returns:
            mail2beyond.framework.BaseParser: Simply returns the `Parser` object by default,
        """
        return parser


class BaseParser:
    """
    Creates a `BaseParser` object that can be used to further parse an `Email` object's content body.

    Attributes:
        name (str): The name of the object. This can be used to differentiate different parser objects from each other.
        mail (mail2beyond.framework.Email): The `Email` object containing the decoded email contents.
        log (logging.Logger): The Logger object to use when logging events that occur when the Parser is called.
        config (dict): The dict of custom `Parser` configuration values. Any extra arguments passed in when the object
            is initially created will be populated here. This can be used to define configurable attributes to your
            custom Parser classes.
    """
    name = ""
    _mail = None
    _config = None

    def __init__(self, mail: Email, **kwargs):
        """
        Initializes the `Parser` object with required attributes.

        Args:
            mail (mail2beyond.framework.Email): The `Email` object containing the decoded email contents.

        Notes:
            Any extra arguments passed in when this object is created will be stored in the 'config' attribute of the
                object.
        """
        self.mail = mail
        self.config = kwargs
        self.log = logging.getLogger(__name__)

    def __str__(self):
        """Sets the string representation of this object."""
        return self.name

    def parse_content(self):
        """
        Initializes the `Parser` object's `parse_content()` method. This method is intended to be overwritten by a child
        class to add parsers for various formats.

        Returns:
            str: By default, this method will simply return the current content decoded content from the 'mail'
                attribute. This method is intended to be overwritten by a child class to extend functionality.
        """
        return self.mail.content

    # Getters and setters
    @property
    def mail(self):
        """The property to get and/or set the  mail attribute."""
        return self._mail

    @mail.setter
    def mail(self, value: Email):
        """Sets the mail attribute after validating the new value."""
        # Ensure value is a mail2beyond.framework.Email object
        if not isinstance(value, Email):
            raise Error("'parser' must be type 'mail2beyond.framework.Email'")

        self._mail = value

    @property
    def subject(self):
        """The property to get and/or set the  subject attribute."""
        return self.mail.headers.get("subject", "No subject")

    @property
    def content(self):
        """Gets the parsed content. This is essentially a shortcut for calling parse_content()."""
        return self.parse_content()

    @property
    def config(self):
        """The property to get and/or set the  config attribute."""
        return self._config

    @config.setter
    def config(self, value: dict):
        """Sets the config attribute after validating the new value."""
        # Ensure config is a dict
        if not isinstance(value, dict):
            raise Error("'config' must be type 'dict'")

        self._config = value
