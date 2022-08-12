"""
Module that contains parsers that parse an email's content body as plaintext. This module simply extends the
mail2beyond.framework.BaseParser class but retains it's default functionality.
"""

from mail2beyond import framework


class Parser(framework.BaseParser):
    """Creates a parser to parse an email's content body as plaintext."""
    name = "text"

    def __init__(self, mail):
        """Initialize this Parser object."""
        super().__init__(mail)
