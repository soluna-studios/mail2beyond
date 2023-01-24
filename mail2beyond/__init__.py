"""
.. include:: ../docs/DOCUMENTATION.md
"""
from . import framework
from . import connectors
from . import parsers
from . import tools

# Set the version of this package
__version__ = "1.0.2"

# Don't include tests module in generated documentation.
__pdoc__ = {"tests": False}
