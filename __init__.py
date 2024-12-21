try:
    import six,cffi,bcrypt,cryptography,pycparser,nacl,paramiko
except (ImportError,ModuleNotFoundError) as e:
    import sys
    import os
    import sublime
    import shutil
    def copytree(src, dst, symlinks=False, ignore=None):
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            try:
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    shutil.copytree(s, d, symlinks, ignore)
                else:
                    if os.path.exists(d):
                        os.remove(d)
                    shutil.copy2(s, d)
            except (PermissionError, FileExistsError):
                pass
    sublime_lib_p38 = os.path.join(sublime.packages_path(),'..','Lib','python38')
    copytree(os.path.join(os.path.dirname(__file__),'dependancies'), sublime_lib_p38)
    sublime_install_path = os.path.join(os.path.dirname(sys.executable),'python3.dll')
    try:
        shutil.copy2(os.path.join(os.path.dirname(__file__),'python3.dll'), sublime_install_path)
    except (PermissionError, FileExistsError):
        pass
    try:
        import six,cffi,bcrypt,cryptography,pycparser,nacl,paramiko
    except (ModuleNotFoundError,ImportError):
        sublime.error_message(f"ssh-panel: dependancy incompatability!\n{e}")

try:
    from .ssh_panel import *
except ImportError:
    import logging
    logging.exception("Error during importing .ssh_panel package")
    raise
