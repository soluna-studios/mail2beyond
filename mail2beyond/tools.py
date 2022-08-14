"""
Module that includes tool functions that primarily assist the CLI and unit tests, but may be useful to others.
"""

import inspect
import logging
import pathlib
import ssl
import sys

from OpenSSL import crypto

import mail2beyond.framework
from . import connectors
from . import parsers
from . import framework


def get_connector_modules(path: (str, None) = None):
    """
    Gathers all available connector modules. This allows a 'path' to be specified to optionally pass in plugin connector
    modules. Built-in connectors are always included.

    Args:
        path (str, None): A path to a directory that contains plugin connector modules. Only .py files within this
            directory will be included. Each .py file must include a class named `Connector` that extends the
            `mail2beyond.framework.BaseConnector class. If `None` is specified, only the built-in connector modules
            will be available.

    Raises:
        mail2beyond.framework.Error: When plugin connector modules could not be loaded.

    Returns:
        dict: A dictionary of available connector modules. The dictionary keys will be the module names and the values
            will be the module itself.
    """
    # Start by gathering the built-in connectors from the mail2beyond.connectors sub-package.
    available_connectors = dict(inspect.getmembers(connectors, inspect.ismodule))

    # If a plugin path was passed in, include modules within that directory as well.
    if path:
        # Convert 'path' into an object
        path_obj = pathlib.Path(path)

        # Require path to be an existing directory
        if not path_obj.exists() or not path_obj.is_dir():
            raise framework.Error(f"failed to load connector modules '{path}' is not an existing directory")

        # Add this directory to our Python path
        sys.path.append(str(path_obj.absolute()))

        # Loop through each .py file in the directory and ensure it is valid
        for module_path in path_obj.glob("*.py"):
            # Verify this module could be imported, contains the Connector class and is added to available connectors.
            try:
                module = __import__(module_path.stem)
                getattr(module, "Connector")
            except ModuleNotFoundError as exc:
                mod_not_found_err_msg = f"failed to import connector module '{module_path.stem}' from '{path}'"
                raise framework.Error(mod_not_found_err_msg) from exc
            except AttributeError as exc:
                attr_err_msg = f"connector module '{module_path.stem}' from '{path}' has no class named 'Connector'"
                raise framework.Error(attr_err_msg) from exc

            # Ensure the module's Connector class is a subclass of BaseConnector
            if inspect.isclass(module.Connector) and issubclass(module.Connector, mail2beyond.framework.BaseConnector):
                available_connectors[module_path.stem] = module
                continue

            # Throw an error if the module's Connector class is not a subclass of BaseConnector
            raise framework.Error(
                f"'Connector' class in '{ module_path }' is not subclass of 'mail2beyond.framework.BaseConnector'"
            )

    # Return the gathered connector modules
    return available_connectors


def get_connectors_from_dict(config: dict, path: (str, None) = None):
    """
    Converts a dictionary representations of connectors to connector objects.
    Args:
        config (dict): A dictionary representation of different connectors to create.
        path (str, None): A path to a directory that contains plugin connector modules. Only .py files within this
            directory will be included. Each .py file must include a class named `Connector` that extends the
            `mail2beyond.framework.BaseConnector` class. If `None` is specified, only the built-in connector modules
            will be available.

    Raises:
        mail2beyond.framework.Error: When a validation error occurs.

    Returns:
        list: A list of Connector objects that can be used.
    """
    # Create a list to store the created connector objects
    valid_connectors = []
    available_connectors = get_connector_modules(path)

    # Require connectors config to be defined
    if "connectors" not in config.keys():
        raise framework.Error("'connectors' value is required")

    # Require connectors config to be a list
    if not isinstance(config.get("connectors"), list):
        raise framework.Error("'connectors' value must be type list")

    # Require at least one connector
    if len(config.get("connectors")) == 0:
        raise framework.Error("at least one 'connectors' item is required")

    # Loop through each connector in the configuration
    for connector in config.get("connectors"):
        # Require connector definition to be a dict
        if not isinstance(connector, dict):
            raise framework.Error("'connectors' items must be type dict")

        # Require connector name to be defined
        if "name" not in connector.keys():
            raise framework.Error("'connectors' items must contain 'name' value")

        # Require connector names to be unique
        for obj in valid_connectors:
            if connector["name"] == obj.name:
                raise framework.Error(f"multiple 'connectors' items assigned name '{obj.name}'")

        # Require connector type to be defined
        if "module" not in connector.keys():
            raise framework.Error("'connectors' configuration items must contain 'module' value")

        # Require connector type to be known
        if connector["module"] not in available_connectors:
            raise framework.Error("'connectors' configuration items must contain 'module' value")

        # Get the connector module that matches this connector
        connector_module = available_connectors.get(connector["module"])

        # Add this connector, it is valid
        connector_obj = connector_module.Connector()
        connector_obj.name = connector.get("name")
        connector_obj.config = connector.get("config", {})

        valid_connectors.append(connector_obj)

    # Return our connector objects
    return valid_connectors


def get_connector_by_name(name, connector_objs):
    """
    Gets the connector with a specific name from a list of Connector objects.

    Args:
        name (str): The name of the connector to find.
        connector_objs (list): A list of Connector objects to search.

    Returns:
        mail2beyond.framework.BaseConnector: The Connector object with the specified name if one was found.
        None: When no Connector object was found with the specified name.
    """
    # Loop through each connector and return the connector with the specified name
    for connector in connector_objs:
        if connector.name == name:
            return connector

    return None


def get_parser_modules(path: (str, None) = None):
    """
    Gathers all available parser modules. This allows a 'path' to be specified to optionally pass in plugin parser
    modules. Built-in parsers are always included.

    Args:
        path (str, None): A path to a directory that contains plugin parser modules. Only .py files within this
            directory will be included. Each .py file must include a class named `Parser` that extends the
            `mail2beyond.framework.BaseParser` class. If `None` is specified, only the built-in parser modules
            will be available.

    Raises:
        mail2beyond.framework.Error: When plugin parser modules could not be loaded.

    Returns:
        dict: A dictionary of available parser modules. The dictionary keys will be the module names and the values
            will be the module itself.
    """
    # Start by gathering the built-in parsers from the mail2beyond.connectors sub-package.
    available_parsers = dict(inspect.getmembers(parsers, inspect.ismodule))

    # If a plugin path was passed in, include modules within that directory as well.
    if path:
        # Convert 'path' into an object
        path_obj = pathlib.Path(path)

        # Require path to be an existing directory
        if not path_obj.exists() or not path_obj.is_dir():
            raise framework.Error(f"failed to load parser modules '{path}' is not an existing directory")

        # Add this directory to our Python path
        sys.path.append(str(path_obj.absolute()))

        # Loop through each .py file in the directory and ensure it is valid
        for module_path in path_obj.glob("*.py"):
            # Verify this module could be imported, contains the Parser class and is added to available connectors.
            try:
                module = __import__(module_path.stem)
                getattr(module, "Parser")
                available_parsers[module_path.stem] = module
            except ModuleNotFoundError as exc:
                mod_not_found_err_msg = f"failed to import parser module '{module_path.stem}' from '{path}'"
                raise framework.Error(mod_not_found_err_msg) from exc
            except AttributeError as exc:
                attr_err_msg = f"parser module '{module_path.stem}' from '{path}' has no class named 'Parser'"
                raise framework.Error(attr_err_msg) from exc

            # Ensure the module's Parser class is a subclass of BaseParser
            if inspect.isclass(module.Parser) and issubclass(module.Parser, mail2beyond.framework.BaseParser):
                available_parsers[module_path.stem] = module
                continue

            # Throw an error if the module's Parser class is not a subclass of BaseParser
            raise framework.Error(
                f"'Parser' class in '{module_path}' is not subclass of 'mail2beyond.framework.BaseParser'"
            )

    # Return the gathered parser modules
    return available_parsers


def get_mappings_from_dict(config: dict, connectors_path: (str, None) = None, parsers_path: (str, None) = None):
    """
    Converts a dictionary representations of mappings to Mapping objects. Since Mapping objects are dependent on
    a Connector object, the dictionary must also include representations of Connector objects to use.

    Args:
        config (dict): A dictionary representation of different mappings to create.
        connectors_path (str, None): A path to a directory that contains plugin connector modules. Only .py files within
            this directory will be included. Each .py file must include a class named `Connector` that extends the
            `mail2beyond.framework.BaseConnector` class. If `None` is specified, only the built-in connector modules
            will be available.
        parsers_path (str, None): A path to a directory that contains plugin parser modules. Only .py files within this
            directory will be included. Each .py file must include a class named `Parser` that extends the
            `mail2beyond.framework.BaseParser` class. If `None` is specified, only the built-in parser modules
            will be available.

    Raises:
        mail2beyond.framework.Error: When a validation error occurs.

    Returns:
        list: A list of Mapping objects that can be used.
    """
    # Variables
    config_connectors = get_connectors_from_dict(config, path=connectors_path)
    available_parsers = get_parser_modules(path=parsers_path)
    valid_mappings = []

    # Require mappings config to be defined
    if "mappings" not in config.keys():
        raise framework.Error("'mappings' value is required")

    # Require mappings config to be a list
    if not isinstance(config.get("mappings"), list):
        raise framework.Error("'mappings' value must be type list")

    # Require at least one mapping
    if len(config.get("mappings")) == 0:
        raise framework.Error("at least one 'mappings' item is required")

    # Loop through each mapping in the configuration
    for mapping in config.get("mappings"):
        # Require mapping definition to be a dict
        if not isinstance(mapping, dict):
            raise framework.Error("'mappings' items must be type dict")

        # Require mapping connector to be defined
        if "connector" not in mapping.keys():
            raise framework.Error("'mappings' items must contain 'connector' value")

        # Get this mapping's connector
        connector = get_connector_by_name(mapping.get("connector"), config_connectors)

        # Require this mapping's connector to exist
        if not connector:
            raise framework.Error(f"'mappings' item references undefined connector '{mapping['connector']}'")

        # Replace the mapping's connector item with the actual object so it can be passed in with kwargs below
        mapping["connector"] = connector

        # Ensure parser is a known
        parser = mapping.get("parser", "auto")
        if parser not in available_parsers:
            raise framework.Error(f"'mappings' item references undefined parser module '{parser}'")

        # Replace the mapping's parser item with the actual Parser class so it can be passed into with kwargs below
        mapping["parser"] = available_parsers.get(parser).Parser

        # Add this mapping, it is valid
        mapping_obj = framework.Mapping(**mapping)
        valid_mappings.append(mapping_obj)

    # Return our connector objects
    return valid_mappings


def get_listeners_from_dict(config: dict, log_level: int = logging.NOTSET, **kwargs):
    """
    Converts a dictionary representations of listeners to Listener objects. Since Listener objects are dependent on
    a Mapping objects, and Mapping objects are dependent on Connector objects, the dictionary must also include
    representations of both Mapping and Connector objects to use.

    Args:
        config (dict): A dictionary representation of different mappings to create.
        log_level (int): Sets the logging level the Listeners' Logger will start logging at. See
            https://docs.python.org/3/library/logging.html#logging-levels
        **connectors_path (str, None): A path to a directory that contains plugin connector modules. Only .py files
            within this directory will be included. Each .py file must include a class named `Connector` that extends
            the`mail2beyond.framework.BaseConnector` class. If `None` is specified, only the built-in connector modules
            will be available.
        **parsers_path (str, None): A path to a directory that contains plugin parser modules. Only .py files within
            this directory will be included. Each .py file must include a class named `Parser` that extends the
            `mail2beyond.framework.BaseParser` class. If `None` is specified, only the built-in parser modules
            will be available.

    Raises:
        mail2beyond.framework.Error: When a validation error occurs.

    Returns:
        list: A list of Listener objects that can be used.
    """
    # Validating listeners from configuration requires many conditions because there are many options.
    # In the future, consider grouping config validation into it's own class with getters and setters.
    # pylint: disable=too-many-branches,too-many-statements

    # Constants
    tls_protocols = {
        "tls1": ssl.TLSVersion.TLSv1,
        "tls1_1": ssl.TLSVersion.TLSv1_1,
        "tls1_2": ssl.TLSVersion.TLSv1_2,
        "tls1_3": ssl.TLSVersion.TLSv1_3
    }
    enable_smtps_default = False
    enable_starttls_default = False
    require_starttls_default = False
    tls_minimum_version_options = tls_protocols.keys()
    tls_minimum_version_default = "tls1_2"

    # Variables
    valid_listeners = []
    mappings = get_mappings_from_dict(
        config,
        connectors_path=kwargs.get("connectors_path"),
        parsers_path=kwargs.get("parsers_path")
    )

    # Require listeners config to be defined.
    if "listeners" not in config.keys():
        raise framework.Error("'listeners' value is required")

    # Require listeners config to be a list
    if not isinstance(config.get("listeners"), list):
        raise framework.Error("'listeners' value must be type list")

    # Require at least one listener
    if len(config.get("listeners")) == 0:
        raise framework.Error("at least one 'listeners' item is required")

    # Loop through each listener and ensure it has a valid configuration.
    for listener in config.get("listeners"):
        # Reset any previous SSLContext
        context = None
        tls_listener = False

        # Require listener definition to be a dict
        if not isinstance(listener, dict):
            raise framework.Error("'listeners' items must be type dict")

        # Ensure listener has an address and port set. The Listener object will validate further upon creation.
        if "address" not in listener.keys():
            raise framework.Error("'listeners' items must contain 'address' value")

        # Ensure listener has an address and port set. The Listener object will validate further upon creation.
        if "port" not in listener.keys():
            raise framework.Error("'listeners' items must contain 'port' value")

        # When 'enable_smtps' is set, ensure it is a bool
        if not isinstance(listener.get("enable_smtps", enable_smtps_default), bool):
            raise framework.Error("'enable_smtps' items must be type bool")

        # Mark this as a TLS enabled listen if SMTPS is enabled
        if listener.get("enable_smtps", enable_smtps_default):
            tls_listener = True

        # When 'enable_starttls' is set, validate associated fields
        if "enable_starttls" in listener.keys():
            # Mark this as a TLS enabled listener
            tls_listener = True

            # Ensure 'enable_smtps' was not also enabled
            if listener.get("enable_smtps", enable_smtps_default):
                raise framework.Error(
                    "'listeners' items 'enable_starttls' and 'enable_smtps' cannot be active on the same listener"
                )

            # Ensure it is a bool
            if not isinstance(listener.get("enable_starttls", enable_starttls_default), bool):
                raise framework.Error("'listeners' item 'enable_starttls' value must be type bool")

            # Check for 'require_starttls' option and ensure it is a bool
            if not isinstance(listener.get("require_starttls", require_starttls_default), bool):
                raise framework.Error("'listeners' item 'require_starttls' value must be type bool")

        # If this was marked as a TLS listener, validate TLS configuration
        if tls_listener:
            # Require the minimum_tls_protocol to be known
            if listener.get("minimum_tls_protocol", tls_minimum_version_default) not in tls_minimum_version_options:
                raise framework.Error("'listeners' item 'minimum_tls_protocol' value is not known protocol")

            # Require a TLS certificate and key
            for field in ["tls_cert", "tls_key"]:
                if field not in listener.keys():
                    raise framework.Error(f"'listeners' item '{field}' is required to use stmps or starttls")

                # Ensure field is string
                if not isinstance(listener.get(field), str):
                    raise framework.Error(f"'listeners' item '{field}' value must be type str")

                # Ensure field is an existing filepath
                if not pathlib.Path(listener.get(field)).exists():
                    raise framework.Error(f"'listeners' item '{field}' is not existing file path")

            # Create the SSLContext for this listener
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            context.load_cert_chain(listener.get("tls_cert"), listener.get("tls_key"))
            context.set_ciphers("HIGH")
            context.minimum_version = tls_protocols[listener.get("tls_minimum_version", tls_minimum_version_default)]

        # Create an SMTPS listener if configured
        if listener.get("enable_smtps", enable_smtps_default):
            valid_listeners.append(
                framework.Listener(
                    mappings=mappings,
                    address=listener.get("address"),
                    port=listener.get("port"),
                    tls_context=context,
                    enable_starttls=False,
                    require_starttls=False,
                    log_level=log_level
                )
            )
        # Create a STARTTLS listener if configured
        elif listener.get("enable_starttls", enable_starttls_default):
            valid_listeners.append(
                framework.Listener(
                    mappings=mappings,
                    address=listener.get("address"),
                    port=listener.get("port"),
                    tls_context=context,
                    enable_starttls=True,
                    require_starttls=listener.get("require_starttls", require_starttls_default),
                    log_level=log_level
                )
            )
        # Create normal SMTP listener otherwise
        else:
            valid_listeners.append(
                framework.Listener(
                    mappings=mappings,
                    address=listener.get("address"),
                    port=listener.get("port"),
                    log_level=log_level
                )
            )

    # Return the validated listeners
    return valid_listeners


def generate_tls_certificate(cert_path: str, key_path: str):
    """
    Generates a self-signed certificate and private key at a specified file path. This is primarily used for unit tests,
    but could be useful elsewhere too.
    Args:
        cert_path (str): The file path to write the generated certificate file to.
        key_path (str): The file path to write the generated key file to.
    """

    # Generate private key
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    # Define self-signed certificate
    cert = crypto.X509()
    cert.get_subject().CN = "example.com"
    cert.set_serial_number(0)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365000)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha512')

    # Write the certificate and key to file
    with open(cert_path, "wt", encoding="utf-8") as cert_file:
        cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))
    with open(key_path, "wt", encoding="utf-8") as key_file:
        key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode("utf-8"))
