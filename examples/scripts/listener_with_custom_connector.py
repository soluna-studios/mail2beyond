import mail2beyond
import requests
import logging


class Connector(mail2beyond.framework.BaseConnector):
    name = "my_custom_connnector"

    def pre_submit(self, parser):
        # Log informational event
        self.log.info("starting 'my_custom_connector's pre_submit()!")

        # Check that the required 'url' attribute is present
        if "url" not in self.config:
            self.log.error("an error occurred validating 'my_custom_connector's 'url' config value!")
            raise mail2beyond.framework.Error("connector 'my_custom_connector' requires config value for 'url'")

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
                json={"msg": f"{subject}\n{content}\n{date}\n{some_specific_header}"},
                timeout=30
            )
            self.log.debug(f"connector 'my_custom_connector' responded with {resp.status_code} status {resp.text}")
        except Exception as req_err:
            self.log.error(f"connector 'my_custom_connector' failed '{req_err}'")
            raise mail2beyond.framework.Error(f"connector 'my_custom_connector' : {req_err}")


# Create a connector object using your custom connector class
custom_connecter = Connector(url="http://myapi.example.com")

# Create a default mapping that uses your custom connector
default_mapping = mail2beyond.framework.Mapping(pattern="default", connector=custom_connecter)

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
