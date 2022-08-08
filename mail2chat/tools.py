"""Holds tool functions that assist the CLI controller and unit tests."""

import inspect
import logging
import pathlib
import ssl

from OpenSSL import crypto

from . import connectors
from . import framework


def get_connectors_from_dict(config: dict):
    """
    Converts dictionary representations of connectors to connector objects.
    :param config: (dict) a dictionary representation of different connectors to create.
    :return: (list) a list of Connector objects that can be used.
    """
    # Create a list to store the created connector objects
    valid_connectors = []
    available_connectors = dict(inspect.getmembers(connectors, inspect.ismodule))

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
        if "connector" not in connector.keys():
            raise framework.Error("'connectors' configuration items must contain 'connector' value")

        # Require connector type to be known
        if connector["connector"] not in available_connectors:
            raise framework.Error("'connectors' configuration items must contain 'connector' value")

        # Get the connector module that matches this connector
        connector_module = available_connectors.get(connector["connector"])

        # Add this connector, it is valid
        connector_obj = connector_module.Connector()
        connector_obj.name = connector.get("name")
        connector_obj.config = connector.get("config", {})

        valid_connectors.append(connector_obj)

    # Return our connector objects
    return valid_connectors


def get_connector_by_name(name, connector_objs):
    """
    Finds the connector with a specific name from a list of connector objects.
    :param name: (str) the name of the connector to fetch.
    :param connector_objs: (list) a list of connector objects to query.
    :return: (Connector) the connector object with the specified name. or None if there was no match.
    """
    # Loop through each connector and return the connector with the specified name
    for connector in connector_objs:
        if connector.name == name:
            return connector

    return None


def get_mappings_from_dict(config: dict):
    """
    Converts dictionary representations of mappings to Mapping objects.
    :param config: (dict) a dictionary representation of different connectors to create.
    :return: (list) a list of Connector objects that can be used.
    """
    # Variables
    config_connectors = get_connectors_from_dict(config)
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

        # Add this mapping, it is valid
        mapping_obj = framework.Mapping(**mapping)
        valid_mappings.append(mapping_obj)

    # Return our connector objects
    return valid_mappings


def get_listeners_from_dict(config: dict, log_level: int = logging.NOTSET):
    """Converts dictionary representations of mappings to Mapping objects.
    :param config: (dict) a dictionary representation of different listeners to create.
    :param log_level: (int) the logging level to configure listeners to use.
    :return: (list) a list of valid Listener objects that can be used.
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
    mappings = get_mappings_from_dict(config)
    valid_listeners = []

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


def generate_tls_certificate(cert_path, key_path):
    """
    Generates a self-signed certificate. This is primarily used for unit tests, but could be useful elsewhere.
    :param cert_path: (str) the file path to store the generated certificate file.
    :param key_path: (str) the file path to store the generated key file.
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
