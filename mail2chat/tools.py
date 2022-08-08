import logging
import ssl
import mail2chat
import inspect
import pathlib
from OpenSSL import crypto


def get_connectors_from_dict(config: dict):
    """
    Converts dictionary representations of connectors to connector objects.
    :param config: (dict) a dictionary representation of different connectors to create.
    :return: (list) a list of Connector objects that can be used.
    """
    # Create a list to store the created connector objects
    valid_connectors = []
    available_connectors = dict(inspect.getmembers(mail2chat.connectors, inspect.ismodule))

    # Require connectors config to be defined
    if "connectors" not in config.keys():
        raise mail2chat.framework.Error("'connectors' value is required")

    # Require connectors config to be a list
    if type(config.get("connectors")) != list:
        raise mail2chat.framework.Error("'connectors' value must be type list")

    # Require at least one connector
    if len(config.get("connectors")) == 0:
        raise mail2chat.framework.Error("at least one 'connectors' item is required")

    # Loop through each connector in the configuration
    for connector in config.get("connectors"):
        # Require connector definition to be a dict
        if type(connector) != dict:
            raise mail2chat.framework.Error("'connectors' items must be type dict")

        # Require connector name to be defined
        if "name" not in connector.keys():
            raise mail2chat.framework.Error("'connectors' items must contain 'name' value")

        # Require connector names to be unique
        for obj in valid_connectors:
            if connector["name"] == obj.name:
                raise mail2chat.framework.Error(f"multiple 'connectors' items assigned name '{obj.name}'")

        # Require connector type to be defined
        if "connector" not in connector.keys():
            raise mail2chat.framework.Error("'connectors' configuration items must contain 'connector' value")

        # Require connector type to be known
        if connector["connector"] not in available_connectors.keys():
            raise mail2chat.framework.Error("'connectors' configuration items must contain 'connector' value")
        else:
            connector_module = available_connectors.get(connector["connector"])

        # Add this connector, it is valid
        connector_obj = connector_module.Connector()
        connector_obj.name = connector.get("name")
        connector_obj.config = connector.get("config", {})

        valid_connectors.append(connector_obj)

    # Return our connector objects
    return valid_connectors


def get_connector_by_name(name, connectors):
    """
    Finds the connector with a specific name from a list of connector objects.
    :param name: (str) the name of the connector to fetch.
    :param connectors: (list) a list of connector objects to query.
    :return: (Connector) the connector object with the specified name. or None if there was no match.
    """
    # Loop through each connector and return the connector with the specified name
    for connector in connectors:
        if connector.name == name:
            return connector


def get_mappings_from_dict(config: dict):
    """
    Converts dictionary representations of mappings to Mapping objects.
    :param config: (dict) a dictionary representation of different connectors to create.
    :return: (list) a list of Connector objects that can be used.
    """
    # Variables
    connectors = get_connectors_from_dict(config)
    valid_mappings = []

    # Require mappings config to be defined
    if "mappings" not in config.keys():
        raise mail2chat.framework.Error("'mappings' value is required")

    # Require mappings config to be a list
    if type(config.get("mappings")) != list:
        raise mail2chat.framework.Error("'mappings' value must be type list")

    # Require at least one mapping
    if len(config.get("mappings")) == 0:
        raise mail2chat.framework.Error("at least one 'mappings' item is required")

    # Loop through each mapping in the configuration
    for mapping in config.get("mappings"):
        # Require mapping definition to be a dict
        if type(mapping) != dict:
            raise mail2chat.framework.Error("'mappings' items must be type dict")

        # Require mapping connector to be defined
        if "connector" not in mapping.keys():
            raise mail2chat.framework.Error("'mappings' items must contain 'connector' value")

        # Get this mapping's connector
        connector = get_connector_by_name(mapping.get("connector"), connectors)

        # Require this mapping's connector to exist
        if not connector:
            raise mail2chat.framework.Error(f"'mappings' item references undefined connector '{mapping['connector']}'")

        # Replace the mapping's connector item with the actual object so it can be passed in with kwargs below
        mapping["connector"] = connector

        # Add this mapping, it is valid
        mapping_obj = mail2chat.framework.Mapping(**mapping)
        valid_mappings.append(mapping_obj)

    # Return our connector objects
    return valid_mappings


def get_listeners_from_dict(config: dict, log_level: int = logging.NOTSET):
    """Converts dictionary representations of mappings to Mapping objects.
    :param config: (dict) a dictionary representation of different listeners to create.
    :param log_level: (int) the logging level to configure listeners to use.
    :return: (list) a list of valid Listener objects that can be used.
    """
    # Constants
    TLS_PROTOCOLS = {
        "tls1": ssl.TLSVersion.TLSv1,
        "tls1_1": ssl.TLSVersion.TLSv1_1,
        "tls1_2": ssl.TLSVersion.TLSv1_2,
        "tls1_3": ssl.TLSVersion.TLSv1_3
    }
    ENABLE_SMTPS_DEFAULT = False
    ENABLE_STARTTLS_DEFAULT = False
    REQUIRE_STARTTLS_DEFAULT = False
    TLS_MINIMUM_VERSION_OPTIONS = TLS_PROTOCOLS.keys()
    TLS_MINIMUM_VERSION_DEFAULT = "tls1_2"

    # Variables
    mappings = get_mappings_from_dict(config)
    valid_listeners = []

    # Require listeners config to be defined.
    if "listeners" not in config.keys():
        raise mail2chat.framework.Error("'listeners' value is required")

    # Require listeners config to be a list
    if type(config.get("listeners")) != list:
        raise mail2chat.framework.Error("'listeners' value must be type list")

    # Require at least one listener
    if len(config.get("listeners")) == 0:
        raise mail2chat.framework.Error("at least one 'listeners' item is required")

    # Loop through each listener and ensure it has a valid configuration.
    for listener in config.get("listeners"):
        # Reset any previous SSLContext
        context = None
        tls_listener = False

        # Require listener definition to be a dict
        if type(listener) != dict:
            raise mail2chat.framework.Error("'listeners' items must be type dict")

        # Ensure listener has an address and port set. The Listener object will validate further upon creation.
        if "address" not in listener.keys():
            raise mail2chat.framework.Error("'listeners' items must contain 'address' value")

        # Ensure listener has an address and port set. The Listener object will validate further upon creation.
        if "port" not in listener.keys():
            raise mail2chat.framework.Error("'listeners' items must contain 'port' value")

        # When 'enable_smtps' is set, ensure it is a bool
        if type(listener.get("enable_smtps", ENABLE_SMTPS_DEFAULT)) != bool:
            raise mail2chat.framework.Error("'enable_smtps' items must be type bool")

        # Mark this as a TLS enabled listen if SMTPS is enabled
        if listener.get("enable_smtps", ENABLE_SMTPS_DEFAULT):
            tls_listener = True

        # When 'enable_starttls' is set, validate associated fields
        if "enable_starttls" in listener.keys():
            # Mark this as a TLS enabled listener
            tls_listener = True

            # Ensure 'enable_smtps' was not also enabled
            if listener.get("enable_smtps", ENABLE_SMTPS_DEFAULT):
                raise mail2chat.framework.Error(
                    "'listeners' items 'enable_starttls' and 'enable_smtps' cannot be active on the same listener"
                )

            # Ensure it is a bool
            if type(listener.get("enable_starttls", ENABLE_STARTTLS_DEFAULT)) != bool:
                raise mail2chat.framework.Error("'listeners' item 'enable_starttls' value must be type bool")

            # Check for 'require_starttls' option and ensure it is a bool
            if type(listener.get("require_starttls", REQUIRE_STARTTLS_DEFAULT)) != bool:
                raise mail2chat.framework.Error("'listeners' item 'require_starttls' value must be type bool")

        # If this was marked as a TLS listener, validate TLS configuration
        if tls_listener:
            # Require the minimum_tls_protocol to be known
            if listener.get("minimum_tls_protocol", TLS_MINIMUM_VERSION_DEFAULT) not in TLS_MINIMUM_VERSION_OPTIONS:
                raise mail2chat.framework.Error("'listeners' item 'minimum_tls_protocol' value is not known protocol")

            # Require a TLS certificate and key
            for field in ["tls_cert", "tls_key"]:
                if field not in listener.keys():
                    raise mail2chat.framework.Error(f"'listeners' item '{field}' is required to use stmps or starttls")

                # Ensure field is string
                if type(listener.get(field)) != str:
                    raise mail2chat.framework.Error(f"'listeners' item '{field}' value must be type str")

                # Ensure field is an existing filepath
                if not pathlib.Path(listener.get(field)).exists():
                    raise mail2chat.framework.Error(f"'listeners' item '{field}' is not existing file path")
                
            # Create the SSLContext for this listener
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            context.load_cert_chain(listener.get("tls_cert"), listener.get("tls_key"))
            context.set_ciphers("HIGH")
            context.minimum_version = TLS_PROTOCOLS[listener.get("tls_minimum_version", TLS_MINIMUM_VERSION_DEFAULT)]

        # Create an SMTPS listener if configured
        if listener.get("enable_smtps", ENABLE_SMTPS_DEFAULT):
            valid_listeners.append(
                mail2chat.framework.Listener(
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
        elif listener.get("enable_starttls", ENABLE_STARTTLS_DEFAULT):
            valid_listeners.append(
                mail2chat.framework.Listener(
                    mappings=mappings,
                    address=listener.get("address"),
                    port=listener.get("port"),
                    tls_context=context,
                    enable_starttls=True,
                    require_starttls=listener.get("require_starttls", REQUIRE_STARTTLS_DEFAULT),
                    log_level=log_level
                )
            )
        # Create normal SMTP listener otherwise
        else:
            valid_listeners.append(
                mail2chat.framework.Listener(
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
    cert.get_subject().CN = "mail2chat.example.com"
    cert.set_serial_number(0)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365000)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha512')

    # Write the certificate and key to file
    with open(cert_path, "wt") as cf:
        cf.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))
    with open(key_path, "wt") as kf:
        kf.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode("utf-8"))
