"""Creates the built-in 'smtp' connector that can be used to forward SMTP message to an upstream SMTP server."""

import smtplib
import socket

from mail2beyond import framework


class Connector(framework.BaseConnector):
    """Defines a connector that forwards received messages to an upstream SMTP server for actual delivery."""
    name = "smtp"

    def submit(self, parser):
        """Overwrites the submit() method to forward the received SMTP message to an upstream SMTP server."""
        # Setup the SMTP client with or without TLS, depending on the configuration
        if self.config.get("smtp_use_tls", False):
            client = smtplib.SMTP_SSL(self.config.get("smtp_host"), self.config.get("smtp_port"))
        else:
            client = smtplib.SMTP(self.config.get("smtp_host"), self.config.get("smtp_port"))

        # Add login credentials to the client if configured
        if self.config.get("smtp_use_login", False):
            client.login(self.config["smtp_login_user"], self.config["smtp_login_password"])

        # Gather information about SMTP connection
        proto = "smtps" if self.config.get("smtp_use_tls", False) else "smtp"
        host = self.config.get("smtp_host")
        port = self.config.get("smtp_port")

        # Send the SMTP message
        try:
            client.sendmail(
                parser.mail.envelope.mail_from,
                parser.mail.envelope.rcpt_tos,
                parser.mail.envelope.content.decode()
            )
            client.close()
            self.log.debug(f"connector '{self}' successfully forwarded message to {proto}://{host}:{port}")
        except Exception as sendmail_error:
            self.log.error(f"connector '{self}' failed to forward message - {sendmail_error}")
            client.close()
            raise sendmail_error

    def pre_submit(self, parser):
        """Overwrites the pre_submit() method to ensure required configuration is set."""
        # Require an 'smtp_host' value to be specified
        if "smtp_host" not in self.config:
            raise framework.Error(f"connector '{self}' requires config value 'smtp_host'")

        # Ensure 'smtp_host' is a str
        if not isinstance(self.config.get("smtp_host"), str):
            raise framework.Error(f"connector '{self}' config value 'smtp_host' must be type 'str'")

        # Require 'smtp_host' to be a valid IP address or hostname
        try:
            socket.gethostbyname(self.config.get("smtp_host"))
        except socket.gaierror as err:
            raise framework.Error(f"connector '{self}' contains invalid 'smtp_host' : {err}")

        # Require an 'smtp_port' value to be specified
        if "smtp_port" not in self.config:
            raise framework.Error(f"connector '{self}' requires config value 'smtp_port'")

        # Require a 'smtp_port' to be integer between 1 adn 65535
        if not isinstance(self.config.get("smtp_port"), int) or 1 > self.config.get("smtp_port") > 65535:
            raise framework.Error(f"connector '{self}' requires config value 'smtp_port' to be between 1 and 65535")

        # Only check the 'smtp_use_tls' value if it is specified otherwise the default will be assumed.
        if "smtp_use_tls" in self.config:
            # Ensure 'smtp_use_tls' is a bool
            if not isinstance(self.config.get("smtp_use_tls"), bool):
                raise framework.Error(f"connector '{self}' config value 'smtp_use_tls' must be type 'bool'")

        # Only check the 'smtp_use_login' requirements if it is specified, otherwise no login will be applied
        if self.config.get("smtp_use_login", False):
            # Require an 'smtp_login_user' value to be specified
            if "smtp_login_user" not in self.config:
                raise framework.Error(f"connector '{self}' requires config value 'smtp_login_user'")

            # Ensure 'smtp_login_user' is a str
            if not isinstance(self.config.get("smtp_login_user"), str):
                raise framework.Error(f"connector '{self}' config value 'smtp_login_user' must be type 'str'")

            # Require an 'smtp_login_password' value to be specified
            if "smtp_login_password" not in self.config:
                raise framework.Error(f"connector '{self}' requires config value 'smtp_login_password'")

            # Ensure 'smtp_login_password' is a str
            if not isinstance(self.config.get("smtp_login_password"), str):
                raise framework.Error(f"connector '{self}' config value 'smtp_login_password' must be type 'str'")
