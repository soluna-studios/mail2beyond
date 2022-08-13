"""
Creates the built-in 'discord' connector that can be used to translate SMTP messages into Discord messages.
"""

import requests

from mail2beyond import framework


class Connector(framework.BaseConnector):
    """Defines a connector that allows mail2beyond to integrate with Discord."""
    name = "discord"

    def submit(self, parser):
        """Overwrites the submit() method to send a Discord message."""
        # Submit this message to Discord via webhook URL
        try:
            resp = requests.post(
                url=self.config["webhook_url"],
                headers={'Content-Type': 'application/json'},
                json={"content": f"*{parser.subject}*\n\n{parser.content}"}
            )
            self.log.debug(f"connector '{self}' responded with {resp.status_code} status {resp.text}")
        except Exception as discord_req_err:
            self.log.error(f"connector '{self}' failed '{discord_req_err}'")
            raise framework.Error(f"connector '{self}' : {discord_req_err}")

    def pre_submit(self, parser):
        """Overwrites the pre_submit() method to ensure required config values are set."""
        # Ensure ths connector has a config value for 'webhook_url'
        if "webhook_url" not in self.config:
            raise framework.Error(f"connector '{self}' requires config value 'webhook_url'")
        # Ensure the webhook_url config value is a string
        if not isinstance(self.config["webhook_url"], str):
            raise framework.Error(f"connector '{self}' config value 'webhook_url' must be type 'str'")
