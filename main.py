import sublime
import sublime_plugin
import os
import json
import re
import time
import zipfile
import sys
import importlib # debug
from .tools import util # debug
importlib.reload(util) # debug
from .tools.util import *

version = "1.3.3"

Dependencies_LOST = False
try:
	from .tools.ssh_controller import *
except Exception as e:
	if isinstance(e, (ImportError,ModuleNotFoundError) if sys.version_info[1] >= 8 else ImportError):
		Dependencies_LOST = True
client_map = {} # client_id -> client
_max_client_id = -1
path_hash_map = {} # remote_path -> (remote_path_hash,local_path,client_id)
icon_data = {} # ext -> "<img class='icon_size' src='res://{icon_path}'>"
icon_style = None # set value with update_icon() (icon_style_data value)
dependencies_source = {
	"github":"github.com/Haiquan-27/SSH-Panel-doc-annex",
	"gitee":"gitee.com/Haiquan27/SSH-Panel-doc-annex"
}
dependencies_url = "https://{source}/releases/download/public/{py_version}_{platform}_{arch}.zip"
icon_style_data = {
	"emjio": { # utf-8 code
		"folder":b'\xf0\x9f\x93\x81'.decode("utf-8"),
		"folder_open":b'\xf0\x9f\x93\x82'.decode("utf-8"),
		"file":b'\xf0\x9f\x93\x84'.decode("utf-8"),
		"menu":b'\xe2\x98\xb0'.decode("utf-8"),
		"drop":b'\xe2\x9c\x96\xef\xb8\x8f'.decode("utf-8"),
		"error":b'\xe2\x9d\x8c'.decode("utf-8"),
		"ok":b'\xe2\x9c\x94\xef\xb8\x8f'.decode("utf-8"),
		"bus":b'\xe2\x8f\xb3'.decode("utf-8"),
		"warning":b'\xe2\x9a\xa0\xef\xb8\x8f'.decode("utf-8"),
		"denied":b'\xf0\x9f\x9a\xab'.decode("utf-8"),
		"dir_symbol": False
	},
	"none":{
		"folder":"",
		"folder_open":"",
		"file":"",
		"menu":"[...]",
		"drop":"[x]",
		"error":"<span class='error'> error</span>",
		"ok":"<span class='keyword'> OK</span>",
		"bus":"<span class='warning'>[###  ]</span>",
		"warning":"<span class='warning'> !</span>",
		"denied":"<span class='error'> denied</span>",
		"dir_symbol": True
	},
	"image":{
		"folder":"<img class='icon_size' src='res://Packages/SSH-Panel/icon/{color}/folder_closed@3x.png'>",
		"folder_open":"<img class='icon_size' src='res://Packages/SSH-Panel/icon/{color}/folder_open@3x.png'>",
		"file":"<img class='icon_size' src='res://Packages/SSH-Panel/icon/{color}/file_type_default@3x.png'>",
		"menu":b'\xe2\x98\xb0'.decode("utf-8"),
		"drop":"[x]",
		"error":" <span class='error'>error</span>",
		"ok":" <span class='keyword'>%s</span>"%b'\xe2\x80\xa2'.decode("utf-8"),
		"bus":" <span style='color:color(var(--greenish) alpha(0.8))'>*</span><span style='color:color(var(--greenish) alpha(1))'>*</span><span style='color:color(var(--greenish) alpha(0.8))'>*</span>",
		"warning":" <span class='warning'>!</span>",
		"denied":" <span class='error'>denied</span>",
		"dir_symbol": False
	}
}

def register_client(client):
	global client_map
	global _max_client_id
	_max_client_id += 1
	new_id = str(_max_client_id)
	client_map[new_id] = client
	return new_id

def update_client(id,client):
	global client_map
	client_map[id] = client

def update_ext_icon():
	global icon_data
	icon_theme = sublime.load_settings(settings_name).get("icon_theme")
	icon_quality = sublime.load_settings(settings_name).get("icon_quality")
	scope_data = sublime.load_settings("scope.json")
	resource_list = sublime.find_resources("*file_type_*%s.png"%icon_quality)
	for path in resource_list:
		file_name = os.path.splitext(os.path.split(path)[1])[0]
		final_scope = file_name[10 : -1*len(icon_quality) if icon_quality else None] if path.startswith(icon_theme) else ""
		if final_scope != "":
			scope_info = scope_data.get(final_scope)
			if scope_info:
				for ext in scope_info["file_extensions"]:
					ext = ext[1:] if ext[0] == os.path.extsep else ext
					icon_data[ext] = "<img class='icon_size' src='res://%s'>"%path

def update_icon():
	update_ext_icon()
	settings = sublime.load_settings(settings_name)
	color = settings.get("icon_color")
	global icon_style_data
	icon_style_data["image"]["folder"] = icon_style_data["image"]["folder"].format(color=color)
	icon_style_data["image"]["folder_open"] = icon_style_data["image"]["folder_open"].format(color=color)
	icon_style_data["image"]["file"] = icon_style_data["image"]["file"].format(color=color)
	global icon_style
	icon_style = icon_style_data.get(settings.get("icon_style"),"none")

def update_color_scheme():
	# 先将当前view样式保存为SSH-Panel.hidden-color-scheme
	view = sublime.active_window().active_view()
	style = view.style()
	new_style_global = {}
	new_style_global["background"] = style.get("background")
	new_style_global["foreground"] = style.get("foreground")
	theme_path = os.path.join(
		sublime.packages_path(),
		"User",
		"SSH-Panel",
		"SSH-Panel.hidden-color-scheme"
	)
	os.makedirs(os.path.split(theme_path)[0],exist_ok=True)
	with open(theme_path,"w") as f:
		f.write(
			json.dumps(
				{
					"globals":new_style_global,
					"variables":{},
					"name":"SSH-Panel"
				},
				indent=5,
				ensure_ascii=False
			)
		)

def plugin_loaded():
	if Dependencies_LOST:
		LOG.I("Dependencies lost , Please exec <span class='keyword'>window.run_command('ssh_panel_install_dependencies')</span> in Sublime Text console")
		sys.stdout.write("Please exec: window.run_command('ssh_panel_install_dependencies')                          # install from github\n")
		sys.stdout.write("         or: window.run_command('ssh_panel_install_dependencies',args={'source':'gitee'})  # install from gitee\n")
	settings = sublime.load_settings(settings_name)
	window = sublime.active_window()
	update_color_scheme()
	# Open ChangeLog
	version_storage_file = os.path.join(
		sublime.packages_path(),
		"User",
		"SSH-Panel",
		"version"
	)
	os.makedirs(os.path.split(version_storage_file)[0],exist_ok=True)
	storage_version = None
	with open(version_storage_file,"a+") as f:
		f.seek(0)
		storage_version = f.read()
		f.seek(0)
		f.truncate()
		f.write(version)
	if storage_version != version:
		window.run_command('open_file', {'file': "${packages}/SSH-Panel/CHANGELOG.md"})
	if sublime.load_settings(settings_name).get("reconnect_on_start"):
		for w in sublime.windows():
			for v in w.views():
				server_name = v.settings().get("ssh_panel_serverName",None)
				if server_name:
					SshPanelCreateConnectCommand(v).run(
						edit = sublime.Edit,
						server_name = server_name,
						connect_now = False,
						reload_from_view = True
					)

def plugin_unloaded():
	pass


class SshPanelSelectConnectCommand(sublime_plugin.WindowCommand):
	def __init__(self,window):
		super().__init__(window)
		self.window = sublime.active_window()
		self.user_config_data = {} # "server_name":(user_config,auth_method)
		self.select = None # (server_name,user_config,error_parameter_list)

	def run(self):
		default_settings = sublime.load_settings(settings_name).get("default_connect_settings")
		for server_name,user_parameter in sublime.load_settings(settings_name).get("server_settings").items():
			user_parameter = UserSettings.format_parameter(default_settings,user_parameter)
			if user_parameter == (None,(None,None)): # 配置参数错误
				self.user_config_data[server_name] = (None,None)
			else:
				self.user_config_data[server_name] = (UserSettings.to_config(*user_parameter),user_parameter[2])
		self.show_panel()

	def show_panel(self,start_index=0):
		show_item_list = []
		server_config_data_items = list(self.user_config_data.items())
		default_settings = sublime.load_settings(settings_name).get("default_connect_settings")
		window = self.window
		for server_name,(user_config,auth_method) in server_config_data_items:
			if int(sublime.version()) >= 4081:
				show_content = [server_name]
				show_content.extend(user_config["remote_path"])
			else:
				show_content = [server_name,str(user_config["remote_path"])]
			show_item_list.append(show_content)

		def on_highlight(index):
			html_ele_tmp = "<tt style='padding-left:10px' class='{style}'>{line}</tt><br>"
			server_name,(user_config,auth_method) = server_config_data_items[index]
			html_ele = "<strong>server parameter of <i>%s</i></strong><br>"%server_name
			error_parameter_list = UserSettings.check_config_error(user_config,auth_method)
			self.select = (server_name,user_config,error_parameter_list)
			for p_name,p_value in user_config.items():
				html_ele += html_ele_tmp.format(
					style='error' if p_name in error_parameter_list else
								'keyword' if p_value != default_settings.get(p_name,None) else
								'info',
					line = "%s : %s"%(p_name,p_value))
			SshPanelOutputCommand(window.active_view()).run(
				edit = sublime.Edit,
				content = html_tmp(content=html_ele),
				is_html = True,
				new_line = False,
				clean = True,
			)

		def on_done(index):
			server_name,user_config,error_parameter_list = self.select
			if index == -1: return
			if error_parameter_list != []: return
			window.destroy_output_panel(output_panel_name)
			SshPanelCreateConnectCommand(window.active_view()).run(
				edit = sublime.Edit,
				server_name = server_name,
				connect_now = True,
				reload_from_view = False
			)
			SshPanelOutputCommand(window.active_view()).run(
				edit = sublime.Edit,
				content = "",
				is_html = False,
				new_line = False,
				clean = True,
			)

		if int(sublime.version()) >= 4081:
			window.show_quick_panel(
				show_item_list,
				on_done,
				sublime.KEEP_OPEN_ON_FOCUS_LOST,
				start_index,
				on_highlight = on_highlight,
				placeholder = "choice you server")
		else:
			window.show_quick_panel(
				show_item_list,
				on_done,
				sublime.KEEP_OPEN_ON_FOCUS_LOST,
				start_index,
				on_highlight = on_highlight,)

class SshPanelEditSettingsCommand(sublime_plugin.WindowCommand):
	def run(self,settings_file):
		if settings_file == "settings":
			example_settings = {
				"server_settings":{
					"MyServer":{
						"hostname":"$0",
						"username":"",
						"password":"",
						"save_password":True,
						"remote_path": ["$HOME"],
						"local_path": "~/SFTP-Local/{auto_generate}",
					},
				}
			}
			self.window.run_command(
				cmd = "edit_settings",
				args = {
				  "base_file": "${packages}/SSH-Panel/ssh-panel.sublime-settings",
				  "default": json.dumps(example_settings,indent=5,ensure_ascii=False)
				})
		elif settings_file == "style":
			self.window.run_command(
				cmd = "edit_settings",
				args = {
				  "base_file": "${packages}/SSH-Panel/style.css",
				  "user_file": "${packages}/User/SSH-Panel/style.css",
				  "default": "/*you can save this file to \"Packages/User/SSH-Panel/style.css\"*/\n" + \
				  			"/*and set \"style_css\": \"Packages/User/SSH-Panel/style.css\" in ssh-panel.sublime-settings*/\n" + \
				  			"/*details https://github.com/Haiquan-27/SSH-Panel#style-coustom*/"
				})

class SshPanelCreateConnectCommand(sublime_plugin.TextCommand):
	def __init__(self,view):
		super().__init__(view)
		self.window = None
		self.PhantomSet = None # phantom 管理器
		self.phantom_items = []
		self.client = None
		self.client_id = None
		self.BUS_LOCK = False
		self.resource_data = None
		self._max_resource_id = 0
		self._user_settings = None
		self.focus_resource = None
		self.navication_view = None
		self.hidden_menu = True

	def run(self,edit,
		server_name: str,
		connect_now: bool,
		reload_from_view: bool
		):
		self.resource_data = {}
		self._max_resource_id = -1
		self.focus_resource = None
		update_icon()
		settings = sublime.load_settings(settings_name)
		self.user_settings = UserSettings()
		self.user_settings.init_from_settings_file(server_name)
		self.window = sublime.active_window()
		if settings.get("new_window",True) and not reload_from_view:
			sublime.active_window().run_command("new_window")
			self.window = sublime.windows()[-1]
			self.window.set_sidebar_visible(False)
		if reload_from_view:
			navication_view = self.view
			self.user_settings.init_from_settings_file(navication_view.settings().get("ssh_panel_serverName"))
		else:
			self.window.set_layout({
				'cells': [
						[0, 0, 1, 1],
						[1, 0, 2, 1]
					],
				'cols': [0.0, 0.2, 1.0],
				'rows': [0.0, 1.0]
			})
			navication_view = self.window.new_file()
			self.window.set_view_index(navication_view,0,0)
			self.window.focus_group(1)
		navication_view.settings().set("ssh_panel_clientID",self.client_id)
		navication_view.settings().set("ssh_panel_serverName",server_name)
		self.init_navcation_view(navication_view)
		self.navication_view = navication_view
		if connect_now:
			self.connect_post(self.reload_list)

	@property
	def user_settings(self):
		return self._user_settings

	@user_settings.setter
	def user_settings(self,value):
		if self.client != None:
			self.client.user_settings = value
		self._user_settings = value

	def init_navcation_view(self,nv):
		nv.set_read_only(True)
		nv.settings().set("word_wrap",False)
		nv.settings().set("gutter",False)
		nv.settings().set("margin",0)
		nv.settings().set("line_numbers",False)
		nv.settings().set("scroll_past_end",False)
		self.PhantomSet = sublime.PhantomSet(nv,"navication_view")
		self.navication_view = nv
		self.update_view_port()

	@async_run
	def connect_post(self,callback=None):
		user_settings = self.user_settings if self.user_settings else UserSettings()
		self._max_resource_id = -1
		self.resource_data = {}
		window = sublime.active_window()
		self.window = window
		loading_bar = SSHPanelLoadingBar("Connecting")
		loading_bar.loading_run()
		with async_Lock:
			client = ClientObj(user_settings)
			if self.client_id:
				update_client(self.client_id,client)
			else:
				self.client_id = register_client(client)
			self.client = client
			# client.connect() 如果需要输入密码，在输入密码后client才可用
			try:
				client.connect(callback)
			except Exception as e:
				raise e
			finally:
				loading_bar.loading_stop()

	def reload_list(self):
		self._max_resource_id = -1
		self.resource_data = {}
		if self.client:
			for remote_path in self.client.user_settings_config["remote_path"]:
				self.add_root_path(path=remote_path,focus=True)
		self.navication_view.settings().erase("color_scheme")
		self.update_view_port()

	def add_path(self,remote_path,root_path):
		resource_data = self.resource_data
		res = []
		try:
		# 使用self.client.get_dir_list会执行两次循环
			for fs in list(self.client.sftp_client.listdir_iter(remote_path)):
				resource_item = {}
				resource_item["name"] = fs.filename
				resource_item["mode"] = oct(stat.S_IMODE(fs.st_mode)).replace("0o","")
				resource_item["is_dir"] = stat.S_ISDIR(fs.st_mode)
				resource_item["root_path"] = root_path
				resource_item["access"] = accessable(fs,*(self.client.userid))
				resource_item["status"] = []
				if resource_item["is_dir"] == True:
					# resource_item["count"] =
					resource_item["expand"] = False # 目录是否展开
				resource_item["focus"] = False # 是否选中
				resource_item["where"] = remote_path
				if self.focus_resource:
					resource_item["depth"] = self.focus_resource["depth"] + 1
				else:
					resource_item["depth"] = 0 # 所在目录深度
				id = self._new_resource_id()
				res.append(id)
				resource_data[id] = resource_item
			return res
		except Exception as e:
			self.update_view_port()
			LOG.E("'%s' is not accessible"%remote_path,str(e.args))

	def _new_resource_id(self):
		self._max_resource_id += 1
		return str(self._max_resource_id)

	def clean_resource(self,resource):
		# 在视图上删除目录资源下的所有资源
		resource_data = self.resource_data
		resource_path = self.rpath_by_resource(resource)
		dl = []
		for id in resource_data.keys():
			r = resource_data[id]
			path_where = r["where"]
			root_path = r["root_path"]
			if path_where.startswith(resource_path) and root_path == resource["root_path"]:
				dl.append(id)
			if root_path == resource_path: # 当在root_path下
				dl.append(id)
		for id in dl:
			del resource_data[id]

	def save_theme(self,data_dict):
		theme_path = os.path.join(
				sublime.packages_path(),
				"User",
				"SSH-Panel",
				"SSH-Panel.hidden-color-scheme"
			)
		os.makedirs(os.path.split(theme_path)[0],exist_ok=True)
		with open(theme_path,"w") as f:
			f.write(
				json.dumps(data_dict,indent=5,ensure_ascii=False)
			)
		return sublime.find_resources("SSH-Panel.hidden-color-scheme")[0]

	@async_run
	def navcation_href_click(self,href):
		# available_operation = [
		# 	"show",
		#	"add_root_path",
		# 	"resource_click",
		# 	"reload",
		# 	"resource_create_file",
		# 	"resource_create_dir",
		# 	"resource_info",
		# 	"resource_delete",
		#	"resource_clone_dir",
		# 	"resource_put_dir",
		# 	"resource_put_file",
		#	"resource_copy_path",
		#	"resource_open_local",
		#	"resource_force_load"
		# ]
		operation,args = href.split(":")
		def reload(what):
			if what == "list":
				self.focus_resource = None
				self.reload_list()
			elif what == "connect":
				self.connect_post(self.reload_list)

		def show(what):
			if what == "info":
				if self.client.user_settings.auth_method == AUTH_METHOD_PASSWORD:
					auth_method = "PASSWORD"
				elif self.client.user_settings.auth_method == AUTH_METHOD_PRIVATEKEY:
					auth_method = "PRIVATEKEY"
				elif self.client.user_settings.auth_method == AUTH_METHOD_GSSAPI:
					auth_method = "GSSAPI"
				html_ele = """
					<p><span class='keyword'>hostname:</span>{hostname}</p>
					<p><span class='keyword'>auth method:</span>{auth_method}</p>
					<p><span class='keyword'>username:</span>{username}</p>
					<p><span class='keyword'>remote platform:</span>{platform}</p>
				""".format(
					hostname = self.client.user_settings_config["hostname"],
					auth_method = auth_method,
					username = self.client.user_settings_config["username"],
					platform = self.client.remote_platform
				)
				SshPanelOutputCommand(self.window.active_view()).run(
					edit = sublime.Edit,
					content = html_tmp(content=html_ele),
					is_html = True,
					new_line = False,
					clean = True,
				)
			if what == "help":
				html_ele = """
					<p><span class='keyword'>[?] </span>Help</p>
					<p><span class='keyword'>[i] </span>Show server infomation</p>
					<p><span class='keyword'>[R] </span>Refresh ans sync file list</p>
					<p><span class='keyword'>[E] </span>Edit settings</p>
					<p><span class='keyword'>[T] </span>Simple terminal</p>
					<p><span class='keyword'>[P] </span>Show panel</p>
					<p><span class='keyword'>[+] </span>Add new root path</p>
					<p><span class='keyword'>[-] </span>Remove root path from view</p>
					<p><span class='keyword'>[...] </span>Object menu</p>
				"""
				SshPanelOutputCommand(self.window.active_view()).run(
					edit = sublime.Edit,
					content = html_tmp(content=html_ele),
					is_html = True,
					new_line = False,
					clean = True,
				)

		def add_root_path(_):
			def on_done(path):
				path = self.client.remote_expandvars(path)
				try:
					if self.client and path not in self.client.user_settings_config["remote_path"]:
						self.add_root_path(path=path,focus=True)
						self.update_view_port()
				except Exception as e:
					LOG.E("Add '%s' Falied %s"%(path,e))
			self.window.show_input_panel(
				"add path:",
				"",
				on_done,
				None,
				None)

		def del_root_path(id):
			dl = [id]
			resource_data = self.resource_data
			root_path = self.rpath_by_resource(resource_data[id])
			for id in resource_data.keys():
				if resource_data[id]["root_path"] == root_path:
					dl.append(id)
			for id in dl:
				del resource_data[id]
			self.update_view_port()

		def run_command(_):
			@async_run
			def on_done(cmd):
				encoding = self.client.user_settings_config.get("terminus_encoding")
				try:
					res = self.client.exec_command(cmd)
					html_ele = "<p><span class='symbol'>$</span>%s</p>"%html_str(cmd)+\
								"<p>%s</p>"%html_str(res[1].read().decode(encoding))+\
								"<p class='error'>%s</p>"%html_str(res[2].read().decode(encoding))
					SshPanelOutputCommand(self.window.active_view()).run(
						edit = sublime.Edit,
						content = html_tmp(content=html_ele),
						is_html = True,
						new_line = True,
						clean = True,
					)
				except Exception as e:
					LOG.E("interattach failed",str(e.args))
			self.window.show_input_panel(
				"cmd:",
				"",
				on_done,
				None,
				None)

		def menu_visible_toggle(_):
			self.hidden_menu = not self.hidden_menu
			self.update_view_port()

		def edit_settings(_):
			SshPanelEditSettingsCommand(self.window).run(
				settings_file = "settings"
			)

		def show_panel(_):
			self.window.run_command("show_panel",args={"panel":"output."+output_panel_name})

		def _resource_create_file(path,fs,parent_resource):
			path = self.client.remote_expandvars(path)
			remote_os_sep = self.client.remote_os_sep
			id = self._new_resource_id()
			# fs = self.client.sftp_client.lstat(path)
			new_resource = {
				"name": path.split(self.client.remote_os_sep)[-1],
				"mode": oct(stat.S_IMODE(fs.st_mode)).replace("0o",""),
				"access": accessable(fs,*(self.client.userid)),
				"is_dir": False,
				"focus": False,
				"status": [],
				"root_path": parent_resource["root_path"] if parent_resource["root_path"] != "" else self.rpath_by_resource(parent_resource),
				"where": remote_os_sep.join(path.split(remote_os_sep)[:-1]),
				"depth": parent_resource["depth"] + 1
			}
			self.resource_data[id] = new_resource
			return new_resource

		def resource_create_file(id):
			resource = self.resource_data[id]
			resource_path = self.rpath_by_resource(resource)
			umask = self.client.umask
			def on_done(path):
				if path[-1] == self.client.remote_os_sep: return
				self.client.sftp_client.open(path,"a").close()
				self.client.sftp_client.chmod(path, 0o666&~umask)
				new = _resource_create_file(
					path,
					self.client.sftp_client.lstat(path),
					resource
				)
				self.update_view_port()
				sublime.status_message("create %s"%self.rpath_by_resource(new))
			self.window.show_input_panel(
				"new file:",
				resource_path+self.client.remote_os_sep,
				on_done,
				None,
				None
			)

		def _resource_create_dir(path,fs,parent_resource):
			remote_os_sep = self.client.remote_os_sep
			path = self.client.remote_expandvars(path)
			id = self._new_resource_id()
			new_resource = {
				"name": path.split(self.client.remote_os_sep)[-1],
				"mode": oct(stat.S_IMODE(fs.st_mode)).replace("0o",""),
				"access": accessable(fs,*(self.client.userid)),
				"is_dir": True,
				"expand": False,
				"focus": False,
				"status" : [],
				"root_path": parent_resource["root_path"] if parent_resource["root_path"] != "" else self.rpath_by_resource(parent_resource),
				"where": remote_os_sep.join(path.split(remote_os_sep)[:-1]),
				"depth": parent_resource["depth"] + 1
			}
			self.resource_data[id] = new_resource
			return new_resource

		def resource_create_dir(id):
			resource = self.resource_data[id]
			resource_path = self.rpath_by_resource(resource)
			umask = self.client.umask
			def on_done(path):
				if path[-1] == self.client.remote_os_sep:
					path = path[:-1]
				self.client.sftp_client.mkdir(path,0o777&~umask)
				new = _resource_create_dir(
					path,
					self.client.sftp_client.lstat(path),
					resource
				)
				self.update_view_port()
				sublime.status_message("create %s"%self.rpath_by_resource(new))
			self.window.show_input_panel(
				"new dir:",
				resource_path+self.client.remote_os_sep,
				on_done,
				None,
				None
			)

		def resource_put_dir(id):
			@async_run
			def callback(dir_list):
				if isinstance(dir_list,str):
					dir_list = [dir_list]
				if not dir_list: return
				select_resource = self.resource_data[id]
				remote_os_sep = self.client.remote_os_sep
				put_path = self.rpath_by_resource(select_resource)
				put_path = put_path[:-1] if put_path[-1] == remote_os_sep else put_path
				self.BUS_LOCK = True
				SUM_D = []
				SUM_F = []
				for local_root in dir_list:
					root_path = os.path.split(local_root)[0]
					LOG.D("put dir","<%s>"%local_root)
					new = _resource_create_dir(
						put_path + remote_os_sep + os.path.split(local_root)[1],
						os.stat(local_root),
						select_resource
					)
					new["focus"] = True
					new["expand"] = True
					new["status"] = ["bus"]
					self.update_view_port()
					for path,_,sub_files in os.walk(local_root):
						rel_path = path[len(root_path):]
						rel_path = rel_path[1:] if rel_path[0] == os.path.sep else rel_path
						rel_remote_path = remote_os_sep.join(rel_path.split(os.path.sep))
						local_dir_path = root_path + os.path.sep + rel_path
						remote_dir_path = put_path + remote_os_sep + rel_remote_path
						fs = os.stat(local_dir_path)
						remote_dir_exists = False
						try:
							self.client.sftp_client.stat(remote_dir_path)
							remote_dir_exists = True
						except FileNotFoundError:
							remote_dir_exists = False
						if not remote_dir_exists:
							self.client.sftp_client.mkdir(
								path = remote_dir_path,
								mode = stat.S_IMODE(fs.st_mode)
							)
						SUM_D.append(remote_dir_path)
						for file in sub_files:
							l_path = local_dir_path + os.path.sep + file
							r_path = remote_dir_path + remote_os_sep + file
							try:
								self.file_sync(l_path, r_path, "put")
								SUM_F.append(r_path)
							except Exception:
								continue
					new["status"] = ["ok"]
					self.update_view_port()
				self.BUS_LOCK = False
				LOG.I("Put %d Folders and %d files"%(len(SUM_D),len(SUM_F)),sorted(SUM_D+SUM_F))
			if int(sublime.version()) >= 4075:
				sublime.select_folder_dialog(callback,multi_select=True)
			else:
				sublime.active_window().show_input_panel(
					"local folder path:",
					"",
					callback,None,None
				)

		def resource_put_file(id):
			select_resource = self.resource_data[id]
			remote_os_sep = self.client.remote_os_sep
			put_path = self.rpath_by_resource(select_resource)
			put_path = put_path[:-1] if put_path[-1] == remote_os_sep else put_path
			def callback(file_list):
				if isinstance(file_list,str):
					file_list = [file_list]
				if len(file_list) == 0: return
				self.BUS_LOCK = True
				for file in file_list:
					l_path = file
					r_path = put_path + remote_os_sep + os.path.split(file)[1]
					try:
						self.file_sync(l_path, r_path, "put")
					except Exception:
						continue
					new = _resource_create_file(
						r_path,
						self.client.sftp_client.stat(r_path),
						select_resource
					) # 创建文件资源
					new["focus"] = True
				self.BUS_LOCK = False
				self.update_view_port()
			if int(sublime.version()) >= 4075:
				sublime.open_dialog(callback,multi_select=True)
			else:
				sublime.active_window().show_input_panel(
					"local file path:",
					"",
					callback,None,None
				)

		def resource_copy_path(id):
			select_resource = self.resource_data[id]
			r_path = self.rpath_by_resource(select_resource)
			l_path = self.lpath_by_resource(select_resource)
			show_list = [r_path,l_path]
			self.window.show_quick_panel(
				show_list,
				lambda i : sublime.set_clipboard(show_list[i]),
				sublime.KEEP_OPEN_ON_FOCUS_LOST
			)

		def resource_clone_dir(id):
			select_resource = self.resource_data[id]
			remote_os_sep = self.client.remote_os_sep
			remote_path = self.rpath_by_resource(select_resource)
			remote_path = remote_path[:-1] if remote_path[-1] == remote_os_sep else remote_path
			root_path = select_resource["root_path"]
			path_hash,local_path_root,_ = path_hash_map.get(root_path if root_path else self.rpath_by_resource(select_resource))
			save_hash_root = os.path.sep.join([local_path_root,path_hash]) # local_path_root/path_hash
			@async_run
			def on_selected(i):
				if i != 0: return # YES
				self.clean_resource(select_resource)
				current_resource = select_resource
				def make_in_local(_remote_path):
					nonlocal current_resource
					new = None
					for fs in list(self.client.sftp_client.listdir_iter(_remote_path)):
						r_path = _remote_path + remote_os_sep + fs.filename
						l_path = save_hash_root + os.path.sep.join(r_path[len(root_path if root_path else select_resource["name"]):].split(remote_os_sep))
						if(stat.S_ISDIR(fs.st_mode)): # 目录
							new = _resource_create_dir(
								r_path,
								fs,
								current_resource
							) # 创建目录资源
							new["expand"] = True
							new["focus"] = False
							new["status"] = ["bus"]
							parent_bak = current_resource.copy()
							current_resource = new
							# 创建空目录，递归进入创建空目录
							os.makedirs(l_path, exist_ok=True)
							os.chmod(l_path,stat.S_IMODE(fs.st_mode))
							make_in_local(r_path) # 递归
							new["status"] = ["ok"]
							current_resource = parent_bak
						else: # 文件
							new = _resource_create_file(
								r_path,
								fs,
								current_resource
							) # 创建文件资源
							new["focus"] = False
							new["status"] = ["bus"]
							# 直接get到本地
							os.makedirs(os.path.split(l_path)[0], exist_ok=True)
							def on_transfer_over(): # 单个文件接收完成
								sublime.status_message("get [%s] to [%s] done"%(r_path,l_path))
								new["status"] = ["ok"]
								self.update_view_port()
							try:
								self.file_sync(l_path,r_path,"get",on_transfer_over)
							except Exception:
								new["status"] = ["error"]
				self.BUS_LOCK = True
				make_in_local(remote_path)
				self.BUS_LOCK = False
				self.update_view_port()
			if int(sublime.version()) >= 4081:
				self.window.show_quick_panel(
					["YES","NO"],
					on_selected,
					sublime.KEEP_OPEN_ON_FOCUS_LOST|sublime.MONOSPACE_FONT,
					placeholder = " clone remote[%s] to local"%remote_path
				)
			else:
				self.window.show_quick_panel(
					["Clone [%s] to local"%remote_path,"clean"],
					on_selected,
					sublime.KEEP_OPEN_ON_FOCUS_LOST|sublime.MONOSPACE_FONT
				)

		def resource_info(id):
			resource = self.resource_data[id]
			resource_path = self.rpath_by_resource(resource)
			resource_stat = self.client.sftp_client.lstat(resource_path)
			size = resource_stat.st_size
			def h_size(size):
				bl = size.bit_length()
				sc = 1 if bl % 10 == 0 else 0
				offset = int(bl/10) - sc
				offset = 0 if offset == -1 else offset
				h_s = str(size >> (offset * 10))
				h_u = ["Bytes","KB","MB","GB","TB","PB"][offset]
				return "%s-%s"%(h_s,h_u)
			html_ele = """
					<p><span class='keyword'>path:</span>{path}</p>
					<p><span class='keyword'>is directory:</span>{is_dir}</p>
					<p><span class='keyword'>uid:</span>{uid}</p>
					<p><span class='keyword'>gid:</span>{gid}</p>
					<p><span class='keyword'>mode:</span>{mode}</p>
					<p><span class='keyword'>size:</span>{size}</p>
					<p><span class='keyword'>access time:</span>{atime}</p>
					<p><span class='keyword'>modify time:</span>{mtime}</p>
				""".format(
					path = resource_path,
					is_dir = resource["is_dir"],
					uid = resource_stat.st_uid,
					gid = resource_stat.st_gid,
					mode = resource["mode"],
					size = "{a:,} ({b})".format(a=size,b=h_size(size)),
					atime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(resource_stat.st_atime)),
					mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(resource_stat.st_mtime)))
			SshPanelOutputCommand(self.window.active_view()).run(
				edit = sublime.Edit,
				content = html_tmp(content=html_ele),
				is_html = True,
				new_line = False,
				clean = True,
			)

		def resource_delete(id):
			resource = self.resource_data[id]
			resource_path = self.rpath_by_resource(resource)
			remote_os_sep = self.client.remote_os_sep
			def confirm():
				if resource["is_dir"]:
					dir_list = [resource_path]
					file_list = []
					denied_list = []
					def walk_dir(_remote_path):
						nonlocal dir_list
						nonlocal file_list
						nonlocal denied_list
						child_list = []
						try:
							child_list = list(self.client.sftp_client.listdir_iter(_remote_path))
						except Exception as e:
							denied_list.append(_remote_path)
						for fs in child_list:
							r_path = _remote_path + remote_os_sep + fs.filename
							if(stat.S_ISDIR(fs.st_mode)): # 目录
								walk_dir(r_path) # 递归
								dir_list.append(r_path)
							else: # 文件
								file_list.append(r_path)
						dir_list.sort()
						file_list.sort()
					walk_dir(resource_path)
					if len(denied_list) != 0:
						resource["status"] = ["warning"]
						LOG.W("Walk %s Falied,cannot access"%(resource_path),denied_list)
						self.update_view_port()
						return
					SUM_F = []
					SUM_D = []
					for fp in file_list:
						try:
							self.client.sftp_client.remove(fp)
							SUM_F.append(fp)
						except Exception as e:
							resource["status"] = ["warning"]
							LOG.W("Delete %s Falied, %s"%(fp,e))
							continue
					for dp in dir_list[::-1]:
						try:
							self.client.sftp_client.rmdir(dp)
							SUM_D.append(dp)
						except Exception as e:
							resource["status"] = ["warning"]
							LOG.W("Delete %s Falied, %s"%(dp,e))
							self.update_view_port()
							break
					LOG.I("Deleted %d Folders and %d files"%(len(SUM_D),len(SUM_F)),sorted(SUM_D+SUM_F))
					if len(SUM_D) + len(SUM_F) == len(dir_list) + len(file_list):
						self.clean_resource(resource)
						del self.resource_data[id]
						self.update_view_port()
				else:
					try:
						self.client.sftp_client.remove(resource_path)
						del self.resource_data[id]
						self.update_view_port()
					except Exception as e:
						resource["status"] = ["denied"]
						self.update_view_port()
						LOG.E("Delete %s Falied, %s"%(resource_path,e))
				sublime.status_message("deleted %s"%resource_path)
			self.window.show_quick_panel(
				["confirm deletion %s"%resource_path,"cancel"],
				lambda i: confirm() if i==0 else None,
				sublime.KEEP_OPEN_ON_FOCUS_LOST|sublime.MONOSPACE_FONT
			)

		def resource_force_load(id):
			select_resource = self.resource_data[id]
			if select_resource["is_dir"]:
				os.makedirs(l_path,exist_ok=True)
			else:
				self.open_resource_file(select_resource,force_load=True)

		def resource_open_local(id):
			select_resource = self.resource_data[id]
			l_path = self.lpath_by_resource(select_resource)
			if select_resource["is_dir"]:
				if os.path.exists(l_path):
					self.window.run_command("open_dir",args= {"dir": l_path})
				else:
					if sublime.yes_no_cancel_dialog("Directory '%s' has not been Get\nCreate in local now?"%l_path) == (sublime.DialogResult.YES if int(sublime.version()) >= 4132 else 1):
						os.makedirs(l_path,exist_ok=True)
						self.window.run_command("open_dir",args= {"dir": l_path})
			else:
				self.window.run_command("open_dir",args= {"dir": os.path.split(l_path)[0],"file":os.path.split(l_path)[1]})

		def resource_click(id):
			try:
				resource_data = self.resource_data
				resource = resource_data[id]
				resource["focus"] = not resource["focus"]
				resource_path = self.rpath_by_resource(resource)
				if resource["focus"]:
					if self.focus_resource and self.focus_resource != resource: # 是否取消上一次的焦点
						self.focus_resource["focus"] = False
					self.focus_resource = resource
				if resource["is_dir"]:
					if resource["focus"] and resource["expand"]:
						resource["focus"] = True
					else:
						resource["expand"] = not resource["expand"] # 另外点击一个展开的无焦点目录，给予焦点且保持展开
						if resource["expand"]:
							if resource["root_path"] != "": # 始终继承父级的root_path
								self.add_path(resource_path,root_path=resource["root_path"])
							else:
								self.add_path(resource_path,root_path=self.rpath_by_resource(resource))
						else:
							self.clean_resource(resource)
				else:
					self.open_resource_file(resource)
				self.update_view_port()
			except Exception as e:
				self.focus_resource["status"] = ["denied"]
				self.update_view_port()
				LOG.E("file access failed",{
					"error": str(e.args)
				})

		def resource_menu(id):
			operation_menu = [
				("Show Info",resource_info),
				("Delete",resource_delete),
				("Copy Path",resource_copy_path),
				("Focus load",resource_force_load),
				("Open Containing Folder…",resource_open_local)
			]
			if self.resource_data[id]["is_dir"]:
				operation_menu.extend([
					("Add File",resource_create_file),
					("Add Folder",resource_create_dir),
					("Clone Folder",resource_clone_dir),
					("Put Folder",resource_put_dir),
					("Put File",resource_put_file)
				])
			if int(sublime.version()) >= 4081:
				self.window.show_quick_panel(
					[d[0] for d in operation_menu],
					lambda i: operation_menu[i][1](id) if i!=-1 else None,
					sublime.KEEP_OPEN_ON_FOCUS_LOST|sublime.MONOSPACE_FONT,
					placeholder = " you can"
				)
			else:
				self.window.show_quick_panel(
					[d[0] for d in operation_menu],
					lambda i: operation_menu[i][1](id) if i!=-1 else None,
					sublime.KEEP_OPEN_ON_FOCUS_LOST|sublime.MONOSPACE_FONT
				)
		if self.BUS_LOCK:
			sublime.message_dialog("SSH-Panel operation busy")
		else:
			with async_Lock:
				# if operation in available_operation:
				eval("{operation}('{args}')".format(operation=operation,args=args))

	def sync_transfer_callback(self,on_done):
		# 负责获取接受sftp put/get进度的callback方法
		# 在完成时调用on_done
		start_t = time.time() - 0.001
		def transfer(load_size,full_size):
			p = load_size/full_size
			full_size = full_size >> 10
			load_size = load_size >> 10
			full_size_s = "{:,}".format(full_size)
			load_size_s = "{:0>{w},}".format(load_size,w=len(full_size_s))
			sublime.status_message("SSH-Panel loading [%s] %s/%skb | %skb/s"%(
				(" "*int(100*p)+str(int(p*100))+"%|").ljust(100," "),
				load_size_s,
				full_size_s,
				"{:,.2f}".format(load_size / (time.time() - start_t))
			))
			if load_size == full_size:
				if on_done:
					on_done()
		return transfer

	def file_sync(self,local_path,remote_path,dir,on_done=None):
		try:
			self.client.file_sync(
				local_path = local_path,
				remote_path = remote_path,
				dir = dir,
				transfer_callback = self.sync_transfer_callback(on_done),
				sync_stat = True
			)
		except Exception as e:
			self.BUS_LOCK = False
			LOG.E("file sync failed",{
				"remote_path":remote_path,
				"local_path": local_path,
				"error": str(e.args)
			})

	def open_resource_file(self,resource,force_load=False):
		remote_path = self.rpath_by_resource(resource)
		local_path  = self.lpath_by_resource(resource)
		LOG.D("path_hash_map",path_hash_map)
		file_reload = sublime.load_settings(settings_name).get("file_reload","auto")
		NF = sublime.TRANSIENT if int(sublime.version()) >= 4096 else (sublime.NewFileFlags.NONE if int(sublime.version()) >= 4132 else 0)
		if os.path.exists(local_path) and file_reload == "auto":
			self.window.open_file(local_path,NF)
			return
		if int(sublime.version()) >= 4081:
			fv = [v for v in self.window.views(include_transient=True) if v.file_name() == local_path]
		else:
			fv = [v for v in self.window.views() if v.file_name() == local_path]
		fv = fv[0] if fv else None
		# load_f 是否载入
		load_f = (file_reload != "never" and (((fv == None or fv.is_dirty() == False) or file_reload == "auto") or file_reload == "always")) or force_load
		if load_f:
			if fv:
				fv.close()
			os.makedirs(os.path.split(local_path)[0], exist_ok=True)
			try:
				self.BUS_LOCK = True
				resource["status"] = ["bus"]
				self.update_view_port()
				def on_transfer_over():
					self.BUS_LOCK = False
					resource["status"] = ["ok"]
					self.update_view_port()
					self.window.open_file(local_path,NF)
				self.file_sync(local_path,remote_path,"get",on_transfer_over)
				if self.client.sftp_client.stat(remote_path).st_size == 0: # sftp_client.py -> _transfer_with_callback : if len(data) == 0: break
					on_transfer_over()
			except Exception as e:
				self.BUS_LOCK = False
				resource["status"] = ["error"]
				self.update_view_port()
				LOG.E("file sync failed",{
					"remote_path":remote_path,
					"local_path": local_path,
					"error": str(e.args)
				})

	def add_root_path(self,path,focus=False):
		id = self._new_resource_id()
		if path[-1] == self.client.remote_os_sep and len(path) != 1:
			path = path[:-1]
		global path_hash_map
		fs = self.client.sftp_client.lstat(path)
		resource = {
			"name": path,
			"mode": oct(stat.S_IMODE(fs.st_mode)).replace("0o",""),
			"access": accessable(fs,*(self.client.userid)),
			"is_dir": True,
			"expand": False,
			"focus": focus,
			"status" : [],
			"root_path": "",
			"where": "",
			"depth": 0
		}
		self.resource_data[id] = resource
		if focus:
			resource["focus"] = not resource["focus"]
			self.focus_resource = resource
			self.navcation_href_click("resource_click:%s"%id)
		path_hash_map[path] = (
				abstract_hex("md5",path.encode("utf8")),
				self.client.user_settings_config["local_path"],
				self.client_id
			)

	def update_view_port(self):
		html_ele = '''
		<p class="title_bar">
			<a class='info' href="menu_visible_toggle:' '">{hostname}<span class='symbol'>@{username}</span></a>
			<p style="display:{btn_display}">
				[<a class='keyword' href="show:info">i</a>]
				[<a class='keyword' href="reload:list">R</a>]
				[<a class='keyword' href="edit_settings:' '">E</a>]
				[<a class='keyword' href="run_command:' '">T</a>]
				[<a class='keyword' href="show_panel:' '">P</a>]
				[<a class='keyword' href="add_root_path:' '">+</a>]
				[<a class='keyword' href="show:help">?</a>]
			</p>
		</p>
		{dirtory_tree}
		<p style="padding-bottom: 100px;"></p>
		'''.format(
				hostname=self.client.user_settings_config["hostname"] if self.client else self.user_settings.config["hostname"],
				username=self.user_settings.config["username"],
				btn_display="none" if self.hidden_menu else "block",
				dirtory_tree=self.render_resource_list()
			)
		phantom = sublime.Phantom(
			sublime.Region(0),
			html_tmp(content=html_ele),
			sublime.LAYOUT_INLINE,
			on_navigate=self.navcation_href_click)
		nv = self.navication_view
		nv.set_name("%s|%s"%(
				self.user_settings.server_name,
				self.rpath_by_resource(self.focus_resource) if self.focus_resource else self.user_settings.server_name if self.client else "connect lost"
			))
		if "SSH-Panel.hidden-color-scheme" not in nv.settings().get("color_scheme",""):
			src_style = nv.style()
			new_style_global = {}
			src_background_color = ""
			theme_dark_color = int(src_style.get("background").replace("#","0x"),16)
			theme_dark_color += int(sublime.load_settings(settings_name).get("nav_bar_color_change"),16)
			theme_dark_color &= 0xffffff
			theme_dark_color = "#{:06x}".format(theme_dark_color)
			new_style_global["background"] = theme_dark_color
			new_style_global["foreground"] = src_style["foreground"]
			new_style_global["line_highlight"] = theme_dark_color
			theme_resource = self.save_theme(
				{
					"globals":new_style_global,
					"variables":{},
					"name":"SSH-Panel"
				}
			)
			nv.settings().set("color_scheme",theme_resource)
		self.phantom_items = [phantom]
		self.update_phantom()
		# LOG.D("resource_data",self.resource_data)

	def update_phantom(self):
		self.PhantomSet.update(self.phantom_items)

	def rpath_by_resource(self,resource,dir_sep=False):
		path_sep = self.client.remote_os_sep
		path = ""
		if resource["where"] != "":
			path = resource["where"]+path_sep+resource["name"]
		else:
			path = resource["name"]
		if dir_sep and resource["is_dir"]:
			path = path + path_sep
		if path.find("//") == 0: # 防止出现"//"开头
			path = path.replace("//","/",1)
		return path

	def lpath_by_resource(self,resource,dir_sep=False):
		global path_hash_map
		remote_path = self.rpath_by_resource(resource)
		remote_os_sep = self.client.remote_os_sep
		path_hash,local_path_root,_ = path_hash_map.get(resource["root_path"]) if resource["root_path"] != "" else path_hash_map.get(resource["name"])
		save_hash_root = os.path.sep.join([local_path_root,path_hash]) # local_path_root/path_hash
		if resource["root_path"] == "":
			local_path = save_hash_root
		elif resource["root_path"] == "/":
			local_path = save_hash_root + os.path.sep.join(remote_path.split(remote_os_sep))
		else:
			local_path = save_hash_root + os.path.sep.join(remote_path.replace(resource["root_path"],"",1).split(remote_os_sep)) # local_path_root/path_hash/remote_mapping_path
		if dir_sep and resource["is_dir"]:
			local_path = local_path + os.path.sep
		return local_path

	def render_resource_list(self):
		if self.client == None or self.client.transport == None:
			return "<a class='debug' href='reload:connect'>no connect</a>"
		ele_list = []
		os_sep_symbol = "<span class='symbol'>%s</span>"%self.client.remote_os_sep if icon_style.get("dir_symbol") else ""
		for resource_id,resource in self.resource_data.items():
			resource_path = self.rpath_by_resource(resource)
			ext = os.path.splitext(resource["name"])[1][1:]
			ele = "<p class='resource_line' style='padding-left:{depth}px'>{file_icon}<a class='{style_class} res' href='resource_click:{resource_id}'>{text}</a>{symbol}{status}<span class='operation_menu'>{operation_menu}</span></p>".format(
					file_icon = (icon_style["folder_open"] if resource["expand"] else icon_style["folder"]) if resource["is_dir"] else icon_data.get(ext,icon_data.get(resource["name"].lower(),icon_style["file"])),
					style_class = " ".join([("res_dir" if resource["is_dir"] else "res_file"),("res_focus" if resource["focus"] else ""),("no_accessible" if not resource["access"] else "")]),
					resource_id = resource_id,
					depth = resource["depth"] * 30,
					text = (resource["name"]).
								replace("&","&amp;").
								replace("<","&lt;").
								replace(">","&gt;").
								replace(" ","&nbsp;"),
					symbol = os_sep_symbol if resource["is_dir"] else "",
					operation_menu = ("<a href='resource_menu:%s'>%s</a>"%(resource_id,icon_style["menu"])) if resource["focus"] else "" +
									  ("<a href='del_root_path:%s'>%s</a>"%(resource_id,icon_style["drop"])) if resource["root_path"] == "" else "",
					status = "".join([icon_style[i] for i in resource["status"]])
				)
			ele_list.append(ele)
		id_re_rule = re.compile(r"(?<=resource_click:)\d+")
		def get_resource_path(ele):
			id = id_re_rule.search(ele).group()
			resource = self.resource_data[id]
			resource_path = self.rpath_by_resource(resource,dir_sep=True)
			if resource["root_path"] == "":
				return resource_path
			else:
				return resource["root_path"] + self.client.remote_os_sep + resource_path
		ele_list.sort(key = get_resource_path)
		return "\n".join(ele_list)

class SshPanelEventCommand(sublime_plugin.ViewEventListener):
	@classmethod
	def is_applicable(self,settings):
		return client_map != {}

	def on_post_save_async(self):
		global path_hash_map
		global client_map
		local_file = self.view.file_name()
		for remote_root,(remote_path_hash,local_root,client_id) in path_hash_map.items():
			local_hash_root = os.path.sep.join([local_root,remote_path_hash])
			if local_file.startswith(local_hash_root):
				client = client_map[client_id]
				remote_file = remote_root + client.remote_os_sep.join(local_file.replace(local_hash_root,"",1).split(os.path.sep))
				if remote_root == client.remote_os_sep: # fix *nix file on '/' will be show '//'
					remote_file = remote_file[1:]
				def upload(remote_file):
					try:
						try:
							client.file_sync(local_file,remote_file,"put",sync_stat=True)
						except:
							client.file_sync(local_file,remote_file,"put")
							LOG.W("file upload success,but stat is not sync")
						sublime.status_message("file upload: "+remote_file)
						LOG.D("save remote",{
							"local_path" : local_file,
							"remote_path": remote_file
						})
					except Exception as e:
						LOG.E("file sync failed",{
							"local_path" : local_file,
							"remote_path": remote_file,
							"error": str(e.args)
						})
				self.view.window().show_input_panel(
					"save to remote:",
					remote_file,
					upload,None,None
				)

	def on_close(self):
		client_id = self.view.settings().get("ssh_panel_clientID",None)
		if client_id:
			global client_map
			global path_hash_map
			client = client_map[client_id]
			client.disconnect()
			for remote_path in client.user_settings_config["remote_path"]:
				del path_hash_map[remote_path]
			del client_map[client_id]

class SshPanelInstallDependenciesCommand(sublime_plugin.WindowCommand):
	def run(self,source="github"):
		if "SSH-Panel.tools.ssh_controller" in sys.modules:
			LOG.I("All modules have been successfully import, no need to download dependencies, Exit")
			return
		py_version = {
			"3":"python3.3",
			"8":"python38"
		}[str(sys.version_info[1])]
		libs_path = ""
		for p in sys.path:
			if p.endswith(os.path.sep.join(["","Lib",py_version])) and os.path.isdir(p):
				if p.endswith(os.path.sep.join(["","Data","Lib",py_version])) or \
				p == os.path.join(os.path.split(sublime.packages_path())[0],"Lib",py_version): # protable version / normal install
					libs_path = p
					break
		if libs_path == "":
			LOG.E("Lib path(%s) not found"%py_version,sys.path)
		self.dependencies_url = dependencies_url.format(
			source = dependencies_source[source],
			py_version = "py%d%d"%sys.version_info[:2], # py33 | py38
			platform = sublime.platform(), # 'osx' | 'linux' | 'windows'
			arch = sublime.arch() # 'x32' | 'x64' | 'arm64'
		)
		zip_pack = os.path.join(libs_path,'sshpaneldep-temp.zip')
		self.libs_path = libs_path
		self.zip_pack = zip_pack
		self.loading_bar = SSHPanelLoadingBar("Downloading")
		self.request_dependencies()

	@async_run
	def request_dependencies(self):
		zip_pack = self.zip_pack
		self.loading_bar.loading_run()
		def on_transfer_over():
			if sublime.yes_no_cancel_dialog("Package download done,unpack and install now?") == sublime.DIALOG_YES:
				self.unpack_install()
				os.remove(self.zip_pack)
				sublime.message_dialog("Package install done,Please restart Sublime Text")
		with async_Lock:
			try:
				urllib.request.urlretrieve(self.dependencies_url,zip_pack,reporthook=self.sync_transfer_callback())
				on_transfer_over()
			except urllib.error.URLError as e:
				SshPanelOutputCommand(self.window.active_view()).run(sublime.Edit,content="",display=False,clean=True)
				if "404" in str(e):
					LOG.E("UNSUPPORTED PLATFORM")
				elif sys.version_info[1] == 8 and isinstance(e.args[0],ssl.SSLCertVerificationError):
					LOG.W("Current SSL Cert Verification cannot be authenticated")
					if sublime.yes_no_cancel_dialog(
							msg = "Current SSL Cert Verification cannot be authenticated,whether to continue?",
							yes_title = "Continue(use unverified)",
							title = "SSH-Panel Install dependencies"
					) == sublime.DIALOG_YES:
						ssl._create_default_https_context = ssl._create_unverified_context
						self.progress_bar(0)
						sublime.status_message("SSH-Panel connecting ...")
						urllib.request.urlretrieve(self.dependencies_url,zip_pack,reporthook=self.sync_transfer_callback())
						on_transfer_over()
				else:
					LOG.I("connot download file: %s"%self.dependencies_url)
			except Exception as e:
				LOG.E("Error %s"%(str(e.args)))
			finally:
				self.loading_bar.loading_stop()

	def progress_bar(self,p):
		self.loading_bar.loading_stop()
		SshPanelOutputCommand(self.window.active_view()).run(
			sublime.Edit,
			content=html_tmp("""
			<p style='width:10000px'>Downloading <span class='keyword'>%s</span></p>
			<p style='width:10000px'>to <span class='keyword'>%s</span></p>
			<p style='width:1000px'>
				<div style='border: 2px solid var(--foreground));width:1000px;height:50px'>
					<div style='background-color:var(--foreground);width:%spx;height:50px'></div>
				</div>
			</p>"""%(self.dependencies_url,self.zip_pack,int(p*1000))),
			is_html=True,
			display=True,
			clean=True,
			new_line=True
		)

	def sync_transfer_callback(self,on_done=None):
		start_t = time.time() - 0.001
		def transfer(load_pack,pack_size,full_size):
			load_size = load_pack * pack_size
			p = load_size/full_size
			full_size = full_size >> 10
			load_size = load_size >> 10
			full_size_s = "{:,}".format(full_size)
			load_size_s = "{:0>{w},}".format(load_size,w=len(full_size_s))
			self.progress_bar(p)
			sublime.status_message("SSH-Panel download %s [%s] %s/%skb | %skb/s"%(
				self.dependencies_url,
				(" "*int(100*p)+str(int(p*100))+"%|").ljust(100," "),
				load_size_s,
				full_size_s,
				"{:,.2f}".format(load_size / (time.time() - start_t))
			))
			if load_size >= full_size:
				if on_done:
					on_done()
		return transfer

	def unpack_install(self):
		unpack_list = []
		with zipfile.ZipFile(self.zip_pack, "r") as zf:
			if "python3.dll" in zf.namelist():
				unpack_list.append("python3.dll")
				try:
					zf.extract("python3.dll",os.path.split(sublime.executable_path())[0])
				except PermissionError as e:
					LOG.I("python3.dll exists,skip")
			for fi in zf.infolist():
				if fi.filename[-1] != "/" and fi.filename.startswith("dist-packages/"):
					fi.filename = fi.filename[14:]
					zf.extract(fi,self.libs_path)
					unpack_list.append(fi.filename)
			LOG.I("unpack file",unpack_list)