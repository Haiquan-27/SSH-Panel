try:
    import six,cffi,bcrypt,cryptography,pycparser,nacl,paramiko
except ModuleNotFoundError as e:
    import os
    import sublime
    import shutil
    def copytree(src, dst, symlinks=False, ignore=None):
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)
    sublime_lib_p38 = os.path.join(sublime.packages_path(),'..','Lib','python38')
    copytree(os.path.join(os.path.dirname(__file__),'dependancies'), sublime_lib_p38)
    try:
        import bcrypt,cffi,cryptography,nacl,six
    except (ModuleNotFoundError,ImportError):
        sublime.error_message(f"ssh-panel: dependancy incompatability!\n{e}")

try:
    from .ssh_panel import *
except ImportError:
    import logging
    logging.exception("Error during importing .ssh_panel package")
    raise
