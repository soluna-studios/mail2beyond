"""
. include:: ./docs/DOCUMENTATION.md
"""
from . import framework
from . import connectors
from . import parsers
from . import tools

# Don't include tests module in generated documentation.
__pdoc__ = {"tests": False}
