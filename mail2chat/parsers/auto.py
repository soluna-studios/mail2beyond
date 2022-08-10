"""
Module that contains a parser that automatically selects another parser based on the mail's content-type header.
"""

from mail2chat import framework
from . import text, html


class Parser(framework.BaseParser):
    """Creates a parser to select the parser that matches this mail's content-type header."""
    name = "auto"

    def __init__(self, mail):
        """Initialize this Parser object."""
        super().__init__(mail)

    def parse_content(self):
        """Automatically selects the parser to use based on the mail's content-type header and parses the content."""
        # Use the html parser if html content type
        print(self.mail.headers.get_content_type().lower())

        if self.mail.headers.get_content_type().lower() == "text/html":
            return html.Parser(self.mail).content

        # Assume the text parser if no match was found
        return text.Parser(self.mail).content
