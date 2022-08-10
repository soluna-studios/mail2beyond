"""
Module that contains parsers that parse an email's content body as plaintext. This module simply extends the
mail2chat.framework.BaseParser class but retains it's default functionality.
"""

import html2text

from mail2chat import framework


class Parser(framework.BaseParser):
    """Creates a parser to parse an email's content body as HTML."""
    name = "html"

    def __init__(self, mail):
        """Initialize this Parser object."""
        super().__init__(mail)

    def parse_content(self):
        """Converts HTML content body to markdown formatted string."""
        return html2text.html2text(html=self.mail.content, bodywidth=len(self.mail.content))
