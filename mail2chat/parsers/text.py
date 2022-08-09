"""
Module that contains parsers that parse an email's content body as plaintext. This module simply extends the
mail2chat.framework.BaseParser class but retains it's default functionality.
"""

from mail2chat import framework


class Parser(framework.BaseParser):
    """Creates a parser to parse an email's content body as plaintext."""

    def __init__(self, mail):
        """Initialize this Parser object."""
        super().__init__(mail)
