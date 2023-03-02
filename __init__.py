import os
import sys
import logging
import sublime

# add dependencies on package initialization
sys.path.append(os.path.join(os.path.dirname(__file__), 'dependencies'))


try:
    import bcrypt,cffi,cryptography,nacl,six
except ModuleNotFoundError as e:
    sublime.error_message("ssh-panel: missing dependencies:\n"+str(e.args))
except ImportError:
    if sublime.platform() == "windows":
        sublime_install_folder = os.dirname(sys.executable)
        target_python3_dll_path = os.path.join(sublime_install_folder,'python3.dll')
        if not os.path.exists(target_python3_dll_path):
            import shutil
            source_python3_dll_path = os.path.join(os.path.dirname(__file__), 'dependencies', 'python3.dll')
            shutil.copy(source_python3_dll_path, target_python3_dll_path)
        try:
            import bcrypt,cffi,cryptography,nacl,six
        except ImportError:
            sublime.error_message("ssh-panel: dependancy incompatability!\n")

try:
    from .ssh_panel import *
except ImportError:
    logging.exception("Error during importing .ssh_panel package")
    raise
