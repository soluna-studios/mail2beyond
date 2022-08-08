from mail2chat import framework
import requests


class Connector(framework.BaseConnector):
    """Defines a connector that allows mail2chat to integrate with Google Chat."""
    name = "google_chat"

    def submit(self, mail, **kwargs):
        """Overwrites the submit() method to send a Google Chat message."""
        # Submit this message to Google Chat via webhook URL
        try:
            resp = requests.post(
                url=self.config["webhook_url"],
                headers={'Content-Type': 'application/json; charset=UTF-8'},
                json={"text": f"*{mail.headers.get('subject')}*\n\n{mail.headers.get_payload()}"}
            )
            self.log.debug(f"connector '{self}' responded with {resp.status_code} status {resp.text}")
        except Exception as google_chat_req_err:
            self.log.error(f"connector '{self}' failed '{google_chat_req_err}'")
            raise framework.Error(f"connector '{self}' : {google_chat_req_err}")

    def pre_submit(self, mail, **kwargs):
        """Overwrites the pre_submit() method to ensure required config values are set."""
        # Ensure ths connector has a config value for 'webhook_url'
        if "webhook_url" not in self.config.keys():
            raise framework.Error(f"connector '{self}' requires config value 'webhook_url'")
        # Ensure the webhook_url config value is a string
        if type(self.config["webhook_url"]) != str:
            raise framework.Error(f"connector '{self}' config value 'webhook_url' must be type 'str'")
