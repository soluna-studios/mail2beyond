"""Creates the built-in 'void' connector that can be used to discard SMTP messages."""
from mail2beyond import framework


class Connector(framework.BaseConnector):
    """Defines a connector that does not do anything."""
    name = "void"

    def submit(self, parser):
        """Overwrites the submit() method, but does nothing."""
        self.log.debug(f"connector '{self}' successfully sent message to the abyss")

    def pre_submit(self, parser):
        """Overwrites the pre_submit() method, but does nothing."""
