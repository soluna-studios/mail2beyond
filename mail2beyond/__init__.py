"""Module that groups all required sub-packages and sub-modules for the mail2beyond package."""
from . import framework
from . import connectors
from . import parsers
from . import tools

# Don't include tests module in generated documentation.
__pdoc__ = {"tests": False}
