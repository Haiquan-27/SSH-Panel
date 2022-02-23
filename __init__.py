import os
import sys

sys.path.append(os.path.dirname(__file__))
# add dependencies on package initialization
sys.path.append(os.path.join(os.path.dirname(__file__), 'dependencies'))


def plugin_loaded():
	pass

def plugin_unloaded():
	pass