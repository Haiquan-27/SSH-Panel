import threading
import sublime_plugin
import sublime
import os
import sys
import hashlib
import base64
import stat
import urllib.request
import ssl

# DEBUG = None
version = "1.3.0"
settings_name = "ssh-panel.sublime-settings"
async_Lock = threading.Lock()
output_panel_phantomSet = None
output_panel_phantom_list = []
output_panel_name = "ssh-panel"
LOG = None

def async_run(func): # 异步运行装饰器
	def wrapper(*args,**kwargs):
		t = threading.Thread(target=func,args=args,kwargs=kwargs,daemon=True).start()
	return wrapper

def accessable(file_stat,user_id,group_ids:()):
	if user_id == 0:
		return True
	file_mod = stat.S_IMODE(file_stat.st_mode)
	if (file_stat.st_uid == user_id and file_mod & 0o700 >= 0o600) or \
		(file_stat.st_gid in group_ids and file_mod & 0o070 >= 0o060) or \
		(file_mod & 0o007 >= 0o006):
		return True
	else:
		return False

def html_tmp(content):
	font_size = sublime.load_settings(settings_name).get("font_size")
	if font_size == "auto":
		font_size = sublime.load_settings("Preferences.sublime-settings").get("font_size",16)
	font_size = int(font_size)
	return """
	<html>
		<style>
		.res{{
			font-size:{f}px;
			line-height:{tlh}px;
		}}
		.resource_line{{
			line-height:{rlh}px;
			padding-bottom:4px;
		}}
		.icon_size{{
			height:{h}px;
			width:{w}px;
		}}
		{css}
		</style>
		<body>
		{content}
		</body>
	</html>
	""".format(
		f = font_size, 			# resource font
		rlh = font_size + 8, 		# resource line height
		tlh = font_size * 1.2,		# resource text line height
		h = 48 * font_size * 0.025, 	# icon height
		w = 54 * font_size * 0.025, 	# icon width
		css = sublime.load_resource(
				sublime.load_settings(settings_name).get("style_css","Packages/SSH-Panel/style.css")
			),
		content = content
	)

def abstract_hex(algorithm:"加密算法 可用 md5 sha256 sha1 ....",value:bytes):
	abstract_algorithm_name = algorithm.lower()
	abstract_algorithm_method = eval("hashlib.%s"%abstract_algorithm_name)
	return abstract_algorithm_method(value).hexdigest()

def abstract_base64(algorithm:"加密算法 可用 md5 sha256 sha1 ....",value:bytes):
	abstract_algorithm_name = algorithm.lower()
	abstract_algorithm_method = eval("hashlib.%s"%abstract_algorithm_name)
	return base64.encodebytes(abstract_algorithm_method(value).digest()).decode("utf8").replace("\n","")
	# base64 -d|openssl [abstract_algorithm_name] -binary |base64

pkex_map = {
	"sha2-nistp256":"sha256",
	"sha2-nistp384":"sha384",
	"sha2-nistp521":"sha512",
	"sha2-512":"sha512",
	"sha2-256":"sha256",
	"sha3-nistp256":"sha3_256",
	"sha3-nistp384":"sha3_384",
	"sha3-nistp521":"sha3_512",
	"sha3-512":"sha3_512",
	"sha3-256":"sha3_256"
}
def pkey_fingerprint(pkey): # 返回paramiko.Pkey的hash base64摘要
	abstract_algorithm_name = "sha256" # default
	for pkex_type in pkex_map.keys():
		if pkey.get_name().endswith(pkex_type): # 根据后缀判断指纹类型
			abstract_algorithm_name = pkex_map[pkex_type]
			# ssh-keyscan -t [kex_name] [host_name] | awk '{print $3}' |base64 -d|openssl [abstract_algorithm_name] -binary |base64
			break
	return (
			abstract_algorithm_name,
			base64.encodebytes(eval("hashlib.%s"%abstract_algorithm_name)(pkey.asbytes()).digest()).decode("utf8").replace("\n",""),
		)

def html_str(s):
	return s.\
	replace("&","&amp;").\
	replace("<","&lt;").\
	replace(">","&gt;").\
	replace(" ","&nbsp;").\
	replace("\n","<br>")

def password_input(callback,on_clean=None):
	input_panel = None
	def hidden(_):
		input_panel.settings().set("color_scheme",'Packages/SSH-Panel/password.hidden-color-scheme')
	input_panel = sublime.active_window().show_input_panel("Password(invisible):","",callback,hidden,on_clean)

class SSHPanelException(Exception):
	pass

class SSHPanelLog():
	def _msg_format(self,msg_type,msg_title,msg_content):
		console_content = "\n" + "SSH-Panel[%s]:%s "%(msg_type,msg_title) + "\n"
		html_ele = {
			"warning":"<p class=warning>Warning:%s</p>"%msg_title,
			"error":"<p class=error>Error:%s</p>"%msg_title,
			"info":"<p class=info>Info:%s</p>"%msg_title,
			"debug":"<p class=debug>Debug:%s</p>"%msg_title,
		}[msg_type]
		if isinstance(msg_content,dict):
			for k,v in msg_content.items():
				console_content += "%s : %s \n"%(k,v)
				html_ele += "<p style='padding-left:10px' class='keyword'>%s: <span>%s</span></p>"%(k,v)
		elif isinstance(msg_content,list):
			for e in msg_content:
				console_content += "%s\n"%(e)
				html_ele += "<p style='padding-left:10px'>%s</p>"%(e)
		else:
			console_content += msg_content
			html_ele += "<p style='padding-left:10px'>%s</p>"%str(msg_content)
		return (console_content,html_tmp(content=html_ele))

	def _log(self,msg_tuple):
		SshPanelOutputCommand(sublime.active_window().active_view()).run(
			sublime.Edit,
			content = msg_tuple[1] if int(sublime.version()) >= 4000 else msg_tuple[0],
			is_html = int(sublime.version()) >= 4000,
			new_line = True,
			clean = False,
			display = not sublime.load_settings(settings_name).get("quiet_log")
		)
		sys.stdout.write(msg_tuple[0] + "\n")

	def W(self,msg_title,msg_content=""):
		msg_tuple = self._msg_format("warning",msg_title,msg_content)
		self._log(msg_tuple)

	def E(self,msg_title,msg_content=""):
		msg_tuple = self._msg_format("error",msg_title,msg_content)
		self._log(msg_tuple)
		raise SSHPanelException("%s\n%s"%(msg_title,msg_tuple[0]))

	def I(self,msg_title,msg_content=""):
		msg_tuple = self._msg_format("info",msg_title,msg_content)
		self._log(msg_tuple)

	def D(self,msg_title,msg_content=""):
		# global DEBUG
		# if DEBUG:
		if sublime.load_settings(settings_name).get("debug_mode"):
			msg_tuple = self._msg_format("debug",msg_title,msg_content)
			self._log(msg_tuple)

LOG = SSHPanelLog()

class SshPanelOutputCommand(sublime_plugin.TextCommand):
	def __init__(self,view):
		super().__init__(view)
		self.panel_view = None

	def run(self,edit,
		content,
		display=True,
		is_html=False,
		new_line=True,
		clean=False):
		window = sublime.active_window()
		panel_view = window.find_output_panel(output_panel_name)
		# window.destroy_output_panel(output_panel_name)
		# panel_view = window.create_output_panel(output_panel_name)
		if not panel_view:
			panel_view = window.create_output_panel(output_panel_name)
			panel_view.set_read_only(True)
			panel_view.settings().set("word_wrap",False)
			panel_view.settings().set("gutter",False)
			panel_view.settings().set("margin",0)
			panel_view.settings().set("line_numbers",False)
			panel_view.settings().set("scroll_past_end",False)
			if panel_view.settings().get("color_scheme",None):
				# panel_view.settings().set("color_scheme",sublime.load_settings("Preferences.sublime-settings").get("color_scheme"))
				panel_view.settings().set("color_scheme",sublime.find_resources("SSH-Panel.hidden-color-scheme")[0])
		self.panel_view = panel_view
		if display:
			window.run_command("show_panel",args={"panel":"output."+output_panel_name})
		panel_view.set_read_only(False)
		global output_panel_phantomSet
		global output_panel_phantom_list
		if not output_panel_phantomSet or output_panel_phantomSet.view != panel_view: # 当phantomSet不存在或phantomSet所在主窗口变化时
			output_panel_phantomSet = sublime.PhantomSet(panel_view)
		if clean:
			# panel_view.erase(edit,sublime.Region(0,panel_view.size()))
			panel_view.run_command("select_all")
			panel_view.run_command("left_delete")
			output_panel_phantom_list = []
			if int(sublime.version()) >= 4000:
				output_panel_phantomSet.update(output_panel_phantom_list)
		if new_line:
			# panel_view.insert(edit,panel_view.size(),"\n")
			panel_view.run_command("insert",args={"characters": "\n"})
		if is_html:
			output_panel_phantom_list.append(
				sublime.Phantom(
					sublime.Region(panel_view.size()),
					content,
					sublime.LAYOUT_INLINE
				)
			)
			output_panel_phantomSet.update(output_panel_phantom_list)
			# panel_view.insert(edit,panel_view.size(),"\n")
			panel_view.run_command("insert",args={"characters": "\n"})
		else:
			# panel_view.insert(edit,panel_view.size(),content.rstrip())
			panel_view.run_command("insert",args={"characters": content.rstrip()})
		panel_view.set_read_only(True)
