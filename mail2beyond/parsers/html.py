"""
Module that contains a parser that parses an email's content body as HTML and converts it to a markdown format.
"""

import html2text

from mail2beyond import framework


class Parser(framework.BaseParser):
    """Creates a parser to parse an email's content body as HTML."""
    name = "html"

    def __init__(self, mail):
        """Initialize this Parser object."""
        super().__init__(mail)

    def parse_content(self):
        """Converts HTML content body to markdown formatted string."""
        return html2text.html2text(html=self.mail.content, bodywidth=len(self.mail.content))
