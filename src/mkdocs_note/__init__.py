from datetime import datetime

__author__ = "virtualguard101"
__description__ = "A MkDocs plugin to add note boxes to your documentation."
__license__ = "GPL-3.0-or-later"
__url__ = "https://github.com/virtualguard101/mkdocs-note"
__email__ = "virtualguard101@gmail.com"
__copyright__ = f"Copyright {datetime.now().year} virtualguard101"

try:
	from ._version import __version__
except ImportError:
	# Fallback for development installations without setuptools-scm
	try:
		from importlib.metadata import version

		__version__ = version("mkdocs-note")
	except ImportError:
		__version__ = "unknown"
