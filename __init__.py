import os
import sys
import logging

# add dependencies on package initialization
sys.path.append(os.path.join(os.path.dirname(__file__), 'dependencies'))


try:
    from .ssh_panel import *
except ImportError:
    logging.exception("Error during importing .ssh_panel package")
    raise
