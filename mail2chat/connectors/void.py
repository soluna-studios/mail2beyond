from mail2chat import framework


class Connector(framework.BaseConnector):
    """Defines a connector that does not do anything."""
    name = "void"

    def submit(self, mail, **kwargs):
        """Overwrites the submit() method, but does nothing."""
        self.log.debug(f"connector '{self}' successfully sent message to the abyss")
        return

    def pre_submit(self, mail, **kwargs):
        """Overwrites the pre_submit() method, but does nothing."""
        return
