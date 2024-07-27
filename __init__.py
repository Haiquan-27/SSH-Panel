import os
import sys
import sublime

def plugin_loaded():
	try:
		import bcrypt,cffi,cryptography,nacl,six
	except ModuleNotFoundError as e:
		sublime.error_message("ssh-panel: missing dependencies:\n"+str(e.args))
	except ImportError:
		if sublime.platform() == "windows":
			sublime.error_message("ssh-panel: missing python3.dll (python3.8)\n")
	# reload connect
	if sublime.load_settings("ssh-panel.sublime-settings").get("reconnect_on_start",False):
		for w in sublime.windows():
			for v in w.views():
				server_name = v.settings().get("ssh_panel_serverName",None)
				if server_name:
					v.run_command("ssh_panel_creat_connect",args={
						"server_name": server_name,
						"connect_now": False,
						"reload_from_view": True
					})