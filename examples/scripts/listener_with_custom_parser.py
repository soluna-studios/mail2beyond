import mail2beyond
import logging


class Parser(mail2beyond.framework.BaseParser):
    name = "my_custom_parser"

    def parse_content(self):
        # Capture the message's content. The self.mail.content cannot be directly modified!
        content = self.mail.content

        # Only include content after a specific keyword
        content = content.split("<SOME KEYWORD>")[1]

        # Mask sensitive content
        content = content.replace("<SOME SENSITIVE CONTENT>", "*****")

        # Return the parsed content
        return content


# Create a connector object using your custom connector class
void_connector = mail2beyond.connectors.void.Connector()

# Create a default mapping that uses your custom connector
default_mapping = mail2beyond.framework.Mapping(pattern="default", connector=void_connector, parser=Parser)

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
