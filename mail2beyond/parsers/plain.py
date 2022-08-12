"""
Module that contains a parser that parse an email's content body as plaintext. This simply extends the
mail2beyond.framework.BaseParser class but retains its default functionality.
"""

from mail2beyond import framework


class Parser(framework.BaseParser):
    """Creates a parser to parse an email's content body as plaintext."""
    name = "text"
