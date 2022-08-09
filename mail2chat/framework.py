"""Contains the base framework classes for mail2chat."""

import email
import inspect
import ipaddress
import re
import logging
import ssl

from aiosmtpd.controller import Controller


class Error(BaseException):
    """Error object used by mail2chat"""
    def __init__(self, message):
        super().__init__()
        self.message = message


class Listener:
    """Creates the listener object that accept SMTP requests and applies logic based on a specified pattern."""
    # Private attributes are not for public consumption.
    # pylint: disable=too-many-instance-attributes

    # Initialize attributes.
    _address = None
    _port = None
    _mappings = None
    _tls_context = None
    _enable_starttls = None
    _require_starttls = None

    def __init__(self, mappings, address="127.0.0.1", port=62125, **kwargs):
        """
        Initializes the object with the required attributes.
        @param mappings: (list) list of Mapping objects to listen for. A 'default' Mapping object must be included.
        @param address: (str) the local IP address the SMTP server should listen on.
        @param port: (int) the local TCP port the SMTP server should listen on.
        @param address: (str) the remote IP address the SMTP server should allow.
        @param port: (int) the remote TCP port the SMTP server should allow.
        @param log_level: (int) the logging level to set.
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
        """Start the listener."""
        self.controller.start()
        self.log.info(f"mail2chat started listening on {self.address}:{self.port}")

    def setup_controller(self):
        """Sets up the controller object with the current address, port and options."""
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

    def setup_logging(self, level=logging.NOTSET, handler=logging.StreamHandler()):
        """
        Sets up the logger for this listener.
        @param level: (int) the logging level to start logging events.
        @param handler: (logging.Handler) the logging handler object to use.
        """

        # Reset the existing logger
        del self.log

        # Set formatting
        log_format = "[%(asctime)s][%(levelname)s]:%(message)s"
        log_date_format = "%b %d %Y %H:%M:%S"

        # Set handler
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

    def get_default_mapping(self, mappings=None):
        """
        Locates the default mapping object from this objects mappings.
        @param mappings: (list) list of mappings to check for a default in
        @return: (Mapping) the mapping object that is the default mapping
        @raise Error: if no mapping is configured as the default
        """
        # Variables
        mappings = mappings if mappings else self.mappings

        # Loop through each mapping and find the default.
        for mapping in mappings:
            if mapping.pattern == "default":
                return mapping

        # Return nothing if no default was found.
        raise Error("mapping with 'default' pattern is required")

    def get_mapping_matches(self, mail):
        """Fetches the mappings that matches the received email.
        @param mail: (Email) the Email object created for the received parser by handle_DATA().
        @return: (list) a list of Mapping objects that matched.
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
        """aiosmtpd method to apply logic for handling data from incoming SMTP message."""
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
            mapping.connector.run(mapping.parser(mail))

        return '250 Message accepted'

    # Getters and setters
    @property
    def address(self):
        """Getter for the address property."""
        return self._address

    @address.setter
    def address(self, value):
        """Setter for the address property."""
        # Require address to be valid IP, or localhost
        if value not in ["localhost"]:
            try:
                ipaddress.ip_address(value)
            except ValueError as exc:
                raise Error("'address' must be valid IP or localhost") from exc

        self._address = value

    @property
    def port(self):
        """Getter for the port property."""
        return self._port

    @port.setter
    def port(self, value):
        """Setter for the port property."""
        # Require port to be valid TCP port
        if isinstance(value, int) and 1 <= value <= 65535:
            self._port = value
        else:
            raise Error("'port' must be valid TCP port")

    @property
    def mappings(self):
        """Getter for the mappings property."""
        return self._mappings

    @mappings.setter
    def mappings(self, value):
        """Getter for the mappings property."""
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
        """Getter for the tls_context property."""
        return self._tls_context

    @tls_context.setter
    def tls_context(self, value):
        """Setter for the tls_context property."""
        # Require tls_context to be SSLContext object or None
        if isinstance(value, ssl.SSLContext) or value is None:
            self._tls_context = value
        else:
            raise Error("'tls_context' must be type 'ssl.SSLContext' or 'None'")

    @property
    def enable_starttls(self):
        """Getter for the enable_starttls property."""
        return self._enable_starttls

    @enable_starttls.setter
    def enable_starttls(self, value):
        """Setter for the enable_starttls property."""
        # Require enable_starttls to be bool
        if isinstance(value, bool):
            self._enable_starttls = value
        else:
            raise Error("'enable_starttls' must be type 'bool'")

    @property
    def require_starttls(self):
        """Getter for the require_starttls property."""
        return self._enable_starttls

    @require_starttls.setter
    def require_starttls(self, value):
        """Setter for the require_starttls property."""
        # Require require_starttls to be bool
        if not isinstance(value, bool):
            raise Error("'require_starttls' must be type 'bool'")

        # Require 'enable_tls' to be True before allowing
        if not self.enable_starttls and value:
            raise Error("'require_starttls' cannot be 'True' while 'enable_starttls' is 'False'")

        self._require_starttls = value


class Mapping:
    """Creates a mapping object that sets parameters to control the formatting and relaying of messages."""
    # Private attributes are not for public consumption.
    # pylint: disable=too-many-instance-attributes

    # Initialize attributes
    _pattern = None
    _field = None
    _connector = None
    _parser = None

    def __init__(self, pattern, connector, **kwargs):
        """
        Initializes the mapping object with desired attributes.
        @param pattern: (str) the regex pattern to use when searching for matches.
        @param connector:
        @param kwargs:
        """
        # Assign required attributes
        self.pattern = pattern
        self.connector = connector

        # Assign optional attributes, or assume defaults.
        self.field = kwargs.get("field", "from")
        self.parser = kwargs.get("parser", BaseParser)

    def __str__(self):
        """Use the pattern as the string representation of this object."""
        return self.pattern

    def is_match(self, value):
        """
        Checks if a specified value matches this mapping.
        @param value: the value to match against.
        @return: (bool) True if the value matches this mapping, False if the value does not match.
        """
        # Check if the value matches this mapping's regex pattern.
        if value is not None and re.search(self.pattern, value):
            return True
        # No match, return False
        return False

    # Getters and setters #
    @property
    def pattern(self):
        """Getter for the pattern property."""
        return self._pattern

    @pattern.setter
    def pattern(self, value):
        """Setter for the pattern property."""
        # Require pattern to be a string
        if isinstance(value, str):
            self._pattern = value
        else:
            raise TypeError("pattern must be type 'str'")

    @property
    def connector(self):
        """Getter for the connector property."""
        return self._connector

    @connector.setter
    def connector(self, value):
        """Setter for the connector property."""
        # Require connector to have a base class of mail2chat.framework.BaseConnector
        if value.__class__.__base__ == BaseConnector:
            self._connector = value
        else:
            raise TypeError("connector must be object with base class 'BaseConnector'")

    @property
    def parser(self):
        """Getter for the parser property."""
        return self._parser

    @parser.setter
    def parser(self, value):
        """Setter for the parser property."""
        # Require parser to have a base class of mail2chat.framework.BaseParser
        if inspect.isclass(value) and hasattr(value, "parse_content"):
            self._parser = value
        else:
            raise TypeError("parser must be a class (not object) with base class 'BaseParser'")

    @property
    def field(self):
        """Getter for the field property."""
        return self._field

    @field.setter
    def field(self, value):
        """Setter for the field property."""
        # Require field to be a support/recognized field
        if isinstance(value, str):
            self._field = value
        else:
            raise ValueError("field must be type 'str'")


class BaseConnector:
    """
    Creates the Mail2ChatConnect base class to be extended by configurable child classes. This establishes standard
    methods and attributes for creating plugin API connectors.
    """
    # Attributes
    name = ""

    def __init__(self, **kwargs):
        """Initialize object attributes"""
        self.config = kwargs
        self.log = logging.getLogger(__name__)

    def __str__(self):
        """Use this objects name attribute as it's string representation."""
        return self.name

    def run(self, parser):
        """
        Runs the current connector object. This method should not be overwritten by child classes.
        @param parser: (Parser) the parser object this connector should use.
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
        @param parser: (Parser) the parser object this connector should use.
        @raise Error: when this method has not been overwritten by a child class.
        """
        raise Error(f"method has not been overwritten by child class but received {parser}")

    def pre_submit(self, parser):
        """
        Initializes the pre_submit() method that is called before the submit() method. In most cases, this should be
        used to validate the config attribute before submit() is actually executed, but can be useful for any other
        logic required. This method should be overrideen by a child class. Otherwise, a warning will be printed.
        @param parser: (Parser) the parser object this connector should use.
        """
        return parser


class Email:
    """Creates an email object that contains the parsed SMTP email."""

    def __init__(self, server, session, envelope, **kwargs):
        """
        Initialize the object with required values.
        @param server:  (Server) the SMTP server object that handled the SMTP session from aiosmtpd
        @param session: (Session) the SMTP session object of the established SMTP session from aiosmtpd
        @param envelope: (Envelope) the envelope object of the received SMTP message from aiosmtpd
        @param parser: (Parser) the Parser object to use when parsing the content body
        """
        self.server = server
        self.session = session
        self.envelope = envelope
        self.headers = email.message_from_bytes(envelope.content)
        self.parser_cls = kwargs.get("parser", BaseParser)

    def get_peer_ip(self):
        """Returns the IP of the remote port"""
        return self.session.peer

    def get_peer_ip_and_port(self):
        """Returns the IP and port of the remote peer in IP:PORT format."""
        return f"{self.session.peer[0]}:{self.session.peer[1]}"

    def get_server_ip_and_port(self):
        """Returns the IP and port of the remote peer in IP:PORT format."""
        return f"{self.server.event_handler.address}:{self.server.event_handler.port}"

    # Getters and setters
    @property
    def content(self):
        """Fetches the decoded and parsed content of the email."""
        return self.parser_cls(self).parse_content()


class BaseParser:
    """Creates a Parser object that can be used to further parse an Email object's content property."""
    name = ""
    _mail = None
    _config = None

    def __init__(self, mail, **kwargs):
        """
        Initialize the Parser object with required attributes.
        @param mail: (mail2chat.framework.Email) the email object created by mail2chat.framework.Listener.handle_DATA
        """
        self.mail = mail
        self.config = kwargs

    def parse_content(self):
        """
        Initializes the Parser object's parse_content() method. By default, this method will simply return the current
        content decoded content from the 'parser' property. This method is intended to be overwritten to add parsers for
        various formats.
        """
        return self.content

    # Getters and setters
    @property
    def mail(self):
        """Getter for the parser property."""
        return self._mail

    @mail.setter
    def mail(self, value):
        """Setter for the parser property."""
        # Ensure value is a mail2chat.framework.Email object
        if not isinstance(value, Email):
            raise Error("'parser' must be type 'mail2chat.framework.Email'")

        self._mail = value

    @property
    def subject(self):
        """Getter for the subject property."""
        return self.mail.headers.get("subject", "No subject")

    @property
    def content(self):
        """Getter for the content property."""
        return self.mail.headers.get_payload(decode=True).decode()

    @property
    def config(self):
        """Getter for the config property."""
        return self._config

    @config.setter
    def config(self, value):
        """Setter for the config property."""
        # Ensure config is a dict
        if not isinstance(value, dict):
            raise Error("'config' must be type 'dict'")

        self._config = value
