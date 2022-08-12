"""
Module that contains a parser that automatically selects another parser based on the mail's content-type header.
"""

from mail2beyond import framework
from . import plain, html


class Parser(framework.BaseParser):
    """Creates a parser to select the parser that matches this mail's content-type header."""
    name = "auto"

    def __init__(self, mail):
        """Initialize this Parser object."""
        super().__init__(mail)

    def parse_content(self):
        """Automatically selects the parser to use based on the mail's content-type header and parses the content."""
        return self.get_parser_by_content_type().content

    def get_parser_by_content_type(self):
        """
        Uses the mail's 'content-type' header to determine which parser to use. In the case there is no match, the
        default 'plain' parser will be used.

        Returns:
            mail2beyond.framework.BaseParser: The Parser object determined to be the best match for the content-type.
        """
        # Fetch our content type
        content_type = self.mail.headers.get_content_type()

        # Use the html parser if html content type
        if self.mail.headers.get_content_type().lower() == "text/html":
            self.log.debug(f"auto parser found 'html' match for content-type '{content_type}'")
            return html.Parser(self.mail)
        # Use the plain parser if plain content type
        if self.mail.headers.get_content_type().lower() == "text/plain":
            self.log.debug(f"auto parser found 'plain' match for content-type '{content_type}'")
            return plain.Parser(self.mail)

        # Assume the text parser if no match was found
        self.log.debug(f"auto parser found no match for content-type '{content_type}' using default 'plain' parser")
        return plain.Parser(self.mail)
