import threading
import sublime_plugin
import sublime
import os
import hashlib
import base64

DEBUG = None

async_Lock = threading.Lock()

output_panel_phantomSet = None
output_panel_phantom_list = []
output_panel_name = "ssh-panel"

def html_tmp(content):
	return """
	<html>
		<style>{css}</style>
		<body>
		{content}
		</body>
	</html>
	""".format(
		css = sublime.load_resource(
				sublime.load_settings("ssh-panel.sublime-settings").get("style_css","Packages/SSH-Panel/style.css")
			),
		content = content
	)

def abstract(algorithm:"加密算法 可用 md5 sha256 sha1 ....",value:bytes):
	abstract_algorithm_name = algorithm.lower()
	abstract_algorithm_method = eval("hashlib.%s"%abstract_algorithm_name)
	return base64.encodebytes(value).decode("utf8").replace("\n","")

def html_str(s):
	return s.\
	replace("&","&amp;").\
	replace("<","&lt;").\
	replace(">","&gt;").\
	replace(" ","&nbsp;").\
	replace("\n","<br>")

class SSHPanelSettingsException(Exception):
	pass

def async_run(func): # 异步运行装饰器
	def wrapper(*args,**kwargs):
		t = threading.Thread(target=func,args=args,kwargs=kwargs,daemon=True).start()
	return wrapper

class SSHPanelLog():
	def _msg_format(self,msg_type,msg_title,msg_content):
		console_content = "\n"+"#"*20+" ssh-panel:[%s] "%msg_type+"#"*20+"\n"
		html_ele = {
			"warning":"<p class=warning>Warning:%s</p>"%msg_title,
			"error":"<p class=error>Error:%s</p>"%msg_title,
			"info":"<p class=info>Info:%s</p>"%msg_title,
			"debug":"<p class=debug>Debug:%s</p>"%msg_title,
		}[msg_type]
		if isinstance(msg_content,dict):
			for k,v in msg_content.items():
				console_content += "%s : %s \n"%(k,v)
				html_ele += "<p style='padding-left:10px' class='keyword'><span>%s:</span>%s</p>"%(k,v)
		elif isinstance(msg_content,list):
			for e in msg_content:
				console_content += "%s\n"%(e)
				html_ele += "<p style='padding-left:10px'>%s</p>"%(e)
		else:
			console_content = msg_content
			html_ele += "<p style='padding-left:10px'>%s</p>"%(msg_content)
		return (console_content,html_tmp(content=html_ele))

	def W(self,msg_title,msg_content=None):
		msg_tuple = self._msg_format("warning",msg_title,msg_content)
		sublime.active_window().run_command(
					cmd="ssh_panel_output",
					args={
						"content": msg_tuple[1],
						"is_html": True,
						"new_line": False,
						"clean": False
					}
				)
		sublime.status_message(msg_title)

	def E(self,msg_title,msg_content=None):
		msg_tuple = self._msg_format("error",msg_title,msg_content)
		sublime.active_window().run_command(
					cmd="ssh_panel_output",
					args={
						"content": msg_tuple[1],
						"is_html": True,
						"new_line": False,
						"clean": True
					}
				)
		sublime.status_message(msg_title)
		raise SSHPanelSettingsException("%s\n%s"%(msg_title,msg_tuple[0]))

	def I(self,msg_title,msg_content=None):
		msg_tuple = self._msg_format("info",msg_title,msg_content)
		sublime.active_window().run_command(
					cmd="ssh_panel_output",
					args={
						"content": msg_tuple[1],
						"is_html": True,
						"new_line": False,
						"clean": False
					}
				)
		sublime.status_message(msg_title)

	def D(self,msg_title,msg_content=None):
		if DEBUG:
			msg_tuple = self._msg_format("debug",msg_title,msg_content)
			sublime.active_window().run_command(
						cmd="ssh_panel_output",
						args={
							"content": msg_tuple[1],
							"is_html": True,
							"new_line": False,
							"clean": False
						}
					)
		sublime.status_message(msg_title)

class SshPanelOutputCommand(sublime_plugin.TextCommand):
	def __init__(self,view):
		super().__init__(view)
		self.panel_view = None

	def run(self,edit,
		content,
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
			if panel_view.settings().get("color_scheme",None):
				panel_view.settings().set("color_scheme",sublime.load_settings("Preferences.sublime-settings").get("color_scheme"))
		self.panel_view = panel_view
		window.run_command("show_panel",args={"panel":"output."+output_panel_name})
		panel_view.set_read_only(False)
		global output_panel_phantomSet
		global output_panel_phantom_list
		if not output_panel_phantomSet or output_panel_phantomSet.view != panel_view: # 当phantomSet不存在或phantomSet所在主窗口变化时
			output_panel_phantomSet = sublime.PhantomSet(panel_view)
		if clean:
			panel_view.erase(edit,sublime.Region(0,panel_view.size()))
			output_panel_phantom_list = []
			if int(sublime.version()) >= 4000:
				output_panel_phantomSet.update(output_panel_phantom_list)
		if new_line:
			panel_view.insert(edit,panel_view.size(),"\n")
		if is_html:
			output_panel_phantom_list.append(
				sublime.Phantom(
					sublime.Region(panel_view.size()),
					content,
					sublime.LAYOUT_INLINE
				)
			)
			try: # st3 bug
				output_panel_phantomSet.update(output_panel_phantom_list)
			except:
				output_panel_phantomSet = sublime.PhantomSet(panel_view)
			panel_view.insert(edit,panel_view.size(),"\n")
		else:
			panel_view.insert(edit,panel_view.size(),content.rstrip())
		panel_view.set_read_only(True)
