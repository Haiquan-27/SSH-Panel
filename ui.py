import sublime
import sublime_plugin
import os
import json
import re
import time
from .ssh_controller import *
from .util import *


client_map = {} # client_id -> client
_max_client_id = -1
path_hash_map = {} # remote_path -> (remote_path_hash,local_path,client_id)
icon_data = {} # ext -> "<img class='icon_size' src='res://{icon_path}'>"
icon_style = None
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
		"error":"<span class='error'>error</span>",
		"ok":"<span class='keyword'> OK</span>",
		"bus":"<span class='warning'>[###  ]</span>",
		"warning":"<span class='warning'> !</span>",
		"denied":"<span class='error'>denied</span>",
		"dir_symbol": True
	},
	"image":{
		"folder":"<img class='icon_size' src='res://Packages/SSH-Panel/icon/{color}/folder_closed@3x.png'>",
		"folder_open":"<img class='icon_size' src='res://Packages/SSH-Panel/icon/{color}/folder_open@3x.png'>",
		"file":"<img class='icon_size' src='res://Packages/SSH-Panel/icon/{color}/file_type_default@3x.png'>",
		"menu":"[...]",
		"drop":"[x]",
		"error":"<span class='error'>error</span>",
		"ok":"<span class='keyword'> OK</span>",
		"bus":"<span class='warning'>[###  ]</span>",
		"warning":"<span class='warning'> !</span>",
		"denied":"<span class='error'>denied</span>",
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
	print(icon_theme)
	# for ext in scope.split("."):
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
	color = sublime.load_settings(settings_name).get("icon_color")
	global icon_style_data
	icon_style_data["image"]["folder"] = icon_style_data["image"]["folder"].format(color=color)
	icon_style_data["image"]["folder_open"] = icon_style_data["image"]["folder_open"].format(color=color)
	icon_style_data["image"]["file"] = icon_style_data["image"]["file"].format(color=color)

def plugin_loaded():
	update_icon()
	if sublime.load_settings(settings_name).get("reconnect_on_start"):
		for w in sublime.windows():
			for v in w.views():
				server_name = v.settings().get("ssh_panel_serverName",None)
				if server_name:
					v.run_command("ssh_panel_create_connect",args={
						"server_name": server_name,
						"connect_now": False,
						"reload_from_view": True
					})

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
			if user_parameter == ({},{},None): # 配置参数错误
				self.user_config_data[server_name] = (None,None)
			else:
				self.user_config_data[server_name] = (UserSettings.to_config(*user_parameter),user_parameter[2])
		self.show_panel()

	def show_panel(self,start_index=0):
		show_item_list = []
		server_config_data_items = list(self.user_config_data.items())
		default_settings = sublime.load_settings(settings_name).get("default_connect_settings")
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
			self.window.run_command(
				cmd="ssh_panel_output",
				args={
					"content": html_tmp(content=html_ele),
					"is_html": True,
					"new_line": False,
					"clean": True
				}
			)

		def on_done(index):
			server_name,user_config,error_parameter_list = self.select
			if index == -1: return
			if error_parameter_list != []: return
			self.window.run_command(
				cmd = "ssh_panel_create_connect",
				args={
					"server_name":server_name,
					"connect_now":True,
					"reload_from_view":False
				}
			)
			self.window.run_command(
				cmd="ssh_panel_output",
				args={
					"content": "",
					"is_html": False,
					"new_line": False,
					"clean": True
				}
			)
			self.window.destroy_output_panel(output_panel_name)

		if int(sublime.version()) >= 4081:
			self.window.show_quick_panel(
				show_item_list,
				on_done,
				sublime.KEEP_OPEN_ON_FOCUS_LOST,
				start_index,
				on_highlight = on_highlight,
				placeholder = "choice you server")
		else:
			self.window.show_quick_panel(
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
		self.resource_data = None
		self._max_resource_id = 0
		self._user_settings = None
		self.focus_resource = None
		self._focus_tip = ""
		self.navication_view = None

	def run(self,edit,
		server_name: str,
		connect_now: bool,
		reload_from_view: bool
		):
		self.resource_data = {}
		self._max_resource_id = -1
		self.focus_resource = None
		settings = sublime.load_settings(settings_name)
		if settings.get("new_window",True):
			sublime.active_window().run_command("new_window")
			window = sublime.windows()[-1]
			window.set_sidebar_visible(False)
			self.window = window
		global icon_style
		icon_style = icon_style_data.get(settings.get("icon_style"),"none")
		window = self.window
		user_settings = UserSettings()
		if reload_from_view:
			navication_view = self.view
			user_settings.init_from_settings_file(navication_view.settings().get("ssh_panel_serverName"))
		else:
			window.set_layout({
				'cells': [
						[0, 0, 1, 1],
						[1, 0, 2, 1]
					],
				'cols': [0.0, 0.2, 1.0],
				'rows': [0.0, 1.0]
			})
			navication_view = window.new_file()
			window.set_view_index(navication_view,0,0)
			window.focus_group(1)
			user_settings.init_from_settings_file(server_name)
		self.user_settings = user_settings
		self.init_navcation_view(navication_view)
		self.navication_view = navication_view

		if connect_now:
			self.connect_post(user_settings)

	@property
	def focus_tip(self): # 取完就清空
		focus_tip = self._focus_tip
		self.focus_tip = ""
		return focus_tip

	@focus_tip.setter
	def focus_tip(self,value):
		self._focus_tip = value

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
	def connect_post(self,user_settings):
		self._max_resource_id = -1
		self.resource_data = {}
		with async_Lock:
			client = ClientObj(user_settings)
			if self.client_id:
				update_client(self.client_id,client)
			else:
				self.client_id = register_client(client)
			self.window.status_message("try to connect")
			client.connect()
			self.window.status_message("connect over")
			self.client = client
			self.navication_view.settings().set("ssh_panel_clientID",self.client_id)
			self.navication_view.settings().set("ssh_panel_serverName",client.user_settings.server_name)
			for remote_path in self.client.user_settings_config["remote_path"]:
				self.add_root_path(path=remote_path,focus=True)
			self.update_view_port()


	def reload_list(self):
		self._max_resource_id = -1
		self.resource_data = {}
		self.navication_view.settings().erase("color_scheme")
		if self.client:
			for remote_path in self.client.user_settings_config["remote_path"]:
				self.add_root_path(path=remote_path,focus=True)
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
				# resource_item["u"] =
				# resource_item["g"] =
				# resource_item["size"] =
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
			self.focus_tip = icon_style["denied"]
			self.update_view_port()
			LOG.E("'%s' is not accessible"%remote_path,str(e.args))

	def _new_resource_id(self):
		self._max_resource_id += 1
		return str(self._max_resource_id)

	def clean_resource(self,resource):
		# 删除目录资源下的所有资源
		resource_data = self.resource_data
		resource_path = self.path_by_resource(resource)
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
		# 	"resource_click",
		# 	"reload",
		# 	"resource_create_file",
		# 	"resource_create_dir",
		# 	"resource_info",
		# 	"resource_delete",
		#	"resource_clone_dir"
		# ]
		operation,args = href.split(":")
		def reload(what):
			if what == "list":
				self.focus_resource = None
				self.reload_list()
			elif what == "connect":
				self.connect_post(self.user_settings)
		def show(what):
			if what == "info":
				if self.client.user_settings.auth_method == AUTH_METHOD_PASSWORD:
					auth_method = "PASSWORD"
				elif self.client.user_settings.auth_method == AUTH_METHOD_PRIVATEKEY:
					auth_method = "PRIVATEKEY"
				elif self.client.user_settings.auth_method == AUTH_METHOD_GSSAPI:
					auth_method = "GSSAPI"
				html_ele = """
					<p><span class='keyword'>hostname:</span>{hostname}<p>
					<p><span class='keyword'>auth method:</span>{auth_method}<p>
					<p><span class='keyword'>username:</span>{username}<p>
					<p><span class='keyword'>remote platform:</span>{platform}<p>
				""".format(
					hostname = self.client.user_settings_config["hostname"],
					auth_method = auth_method,
					username = self.client.user_settings_config["username"],
					platform = self.client.remote_platform
				)
				self.window.run_command(
					cmd="ssh_panel_output",
					args={
						"content": html_tmp(content=html_ele),
						"is_html": True,
						"new_line": False,
						"clean": True
					}
				)
			if what == "help":
				html_ele = """
					<p><span class='keyword'>[?] </span>Help<p>
					<p><span class='keyword'>[i] </span>Show server infomation<p>
					<p><span class='keyword'>[R] </span>Refresh ans sync file list<p>
					<p><span class='keyword'>[E] </span>Edit settings<p>
					<p><span class='keyword'>[T] </span>Simple terminal<p>
					<p><span class='keyword'>[P] </span>Show panel<p>
					<p><span class='keyword'>[+] </span>Add new root path<p>
					<p><span class='keyword'>[-] </span>Remove root path from view<p>
					<p><span class='keyword'>[...] </span>Object menu<p>
				"""
				self.window.run_command(
					cmd="ssh_panel_output",
					args={
						"content": html_tmp(content=html_ele),
						"is_html": True,
						"new_line": False,
						"clean": True
					}
				)
		def add_root_path(_):
			def on_done(path):
				if self.client and path not in self.client.user_settings_config["remote_path"]:
					self.add_root_path(path=path,focus=True)
					self.update_view_port()
			self.window.show_input_panel(
				"add path:",
				"",
				on_done,
				None,
				None)

		def del_root_path(id):
			dl = [id]
			resource_data = self.resource_data
			root_path = self.path_by_resource(resource_data[id])
			for id in resource_data.keys():
				if resource_data[id]["root_path"] == root_path:
					dl.append(id)
			for id in dl:
				del resource_data[id]
			self.update_view_port()

		def run_command(_):
			@async_run
			def on_done(cmd):
				try:
					res = self.client.exec_command(cmd)
					html_ele = "<p><span class='symbol'>$</span>%s</p>"%html_str(cmd)+\
								"<p>%s</p>"%html_str(res[1].read().decode("utf8"))+\
								"<p class='error'>%s</p>"%html_str(res[2].read().decode("utf8"))
					self.window.run_command(
						cmd="ssh_panel_output",
						args={
								"content": html_tmp(content=html_ele),
								"is_html": True,
								"new_line": True,
								"clean": False
							}
						)
				except Exception as e:
					LOG.E("interattach failed",str(e.args))
			self.window.show_input_panel(
				"cmd:",
				"",
				on_done,
				None,
				None)
		def edit_settings(_):
			self.window.run_command("ssh_panel_edit_settings",args={
				"settings_file": "settings"
			})
		def show_panel(_):
			self.window.run_command("show_panel",args={"panel":"output."+output_panel_name})
		def _resource_create_file(path,fs,parent_resource):
			path = self.client.remote_expandvars(path)
			# f =  self.client.sftp_client.open(path,"a")
			# f.close()
			id = self._new_resource_id()
			# fs = self.client.sftp_client.lstat(path)
			new_resource = {
				"name": os.path.split(path)[-1],
				"mode": oct(stat.S_IMODE(fs.st_mode)).replace("0o",""),
				"access": accessable(fs,*(self.client.userid)),
				"is_dir": False,
				"focus": False,
				"root_path": parent_resource["root_path"] if parent_resource["root_path"] != "" else self.path_by_resource(parent_resource),
				"where": os.path.split(path)[0],
				"depth": parent_resource["depth"] + 1
			}
			self.resource_data[id] = new_resource
			return new_resource
		def resource_create_file(id):
			resource = self.resource_data[id]
			resource_path = self.path_by_resource(resource)
			def on_done(path):
				if path[-1] == self.client.remote_os_sep: return
				f =  self.client.sftp_client.open(path,"a")
				f.close()
				new = _resource_create_file(
					path,
					self.client.sftp_client.lstat(path),
					resource
				)
				self.update_view_port()
				sublime.status_message("create %s"%self.path_by_resource(new_resource))
			self.window.show_input_panel(
				"new file:",
				resource_path+self.client.remote_os_sep,
				on_done,
				None,
				None)
		def _resource_create_dir(path,fs,parent_resource):
			path = self.client.remote_expandvars(path)
			id = self._new_resource_id()
			# fs = self.client.sftp_client.lstat(path)
			new_resource = {
				"name": os.path.split(path)[-1],
				"mode": oct(stat.S_IMODE(fs.st_mode)).replace("0o",""),
				"access": accessable(fs,*(self.client.userid)),
				"is_dir": True,
				"expand": False,
				"focus": False,
				"root_path": parent_resource["root_path"] if parent_resource["root_path"] != "" else self.path_by_resource(parent_resource),
				"where": os.path.split(path)[0],
				"depth": parent_resource["depth"] + 1
			}
			self.resource_data[id] = new_resource
			return new_resource
		def resource_create_dir(id):
			resource = self.resource_data[id]
			resource_path = self.path_by_resource(resource)
			def on_done(path):
				if path[-1] == self.client.remote_os_sep:
					path = path[:-1]
				self.client.sftp_client.mkdir(path)
				new = _resource_create_dir(
					path,
					self.client.sftp_client.lstat(path),
					resource
				)
				self.update_view_port()
				sublime.status_message("create %s"%self.path_by_resource(new))
			self.window.show_input_panel(
				"new dir:",
				resource_path+self.client.remote_os_sep,
				on_done,
				None,
				None)
		def resource_clone_dir(id):
			select_resource = self.resource_data[id]
			path_hash,local_path_root,_ = path_hash_map.get(select_resource["root_path"])
			save_hash_root = os.path.sep.join([local_path_root,path_hash]) # local_path_root/path_hash
			remote_path = self.path_by_resource(select_resource)

			@async_run
			def on_done(i):
				self.clean_resource(select_resource)
				current_resource = select_resource
				def make_in_local(_remote_path):
					nonlocal current_resource
					self.focus_tip = icon_style["bus"]
					for fs in list(self.client.sftp_client.listdir_iter(_remote_path)): # 必须要转列表否则单个生成式遍历对象会超时
						r_path = _remote_path + self.client.remote_os_sep + fs.filename
						l_path = save_hash_root + os.path.sep.join(r_path.split(self.client.remote_os_sep))
						if(stat.S_ISDIR(fs.st_mode)): # 目录
							new = _resource_create_dir(
								r_path,
								fs,
								current_resource
							) # 创建目录资源
							new["expand"] = True
							new["focus"] = True
							parent_bak = current_resource.copy()
							current_resource = new
							# 创建空目录，递归进入创建空目录
							os.makedirs(l_path, exist_ok=True)
							os.chmod(l_path,stat.S_IMODE(fs.st_mode))
							print(r_path,"**")
							make_in_local(r_path) # 递归
							current_resource = parent_bak
						else: # 文件
							new = _resource_create_file(
								r_path,
								fs,
								current_resource
							) # 创建文件资源
							new["focus"] = True
							# 直接get到本地
							os.makedirs(os.path.split(l_path)[0], exist_ok=True)
							self.client.file_sync(l_path,r_path,dir="get",sync_stat=True)
							print(r_path)
							pass
						sublime.status_message("get [%s] to [%s]"%(r_path,l_path))
						self.update_view_port()
				make_in_local(remote_path)
				self.focus_tip = icon_style["ok"]
				self.update_view_port()
			if int(sublime.version()) >= 4081:
				self.window.show_quick_panel(
					["yes","no"],
					on_done,
					sublime.KEEP_OPEN_ON_FOCUS_LOST|sublime.MONOSPACE_FONT,
					placeholder = " clone remote[%s] to local"%remote_path
				)
			else:
				self.window.show_quick_panel(
					["clone [%s] to local"%get_path,"clean"],
					on_done,
					sublime.KEEP_OPEN_ON_FOCUS_LOST|sublime.MONOSPACE_FONT
				)

		def resource_info(id):
			resource = self.resource_data[id]
			resource_path = self.path_by_resource(resource)
			resource_stat = self.client.sftp_client.lstat(resource_path)
			html_ele = """
					<p><span class='keyword'>path:</span>{path}<p>
					<p><span class='keyword'>is directory:</span>{is_dir}<p>
					<p><span class='keyword'>uid:</span>{uid}<p>
					<p><span class='keyword'>gid:</span>{gid}<p>
					<p><span class='keyword'>mode:</span>{mode}<p>
					<p><span class='keyword'>size:</span>{size}<p>
					<p><span class='keyword'>access time:</span>{atime}<p>
					<p><span class='keyword'>modify time:</span>{mtime}<p>
				""".format(
					path = resource_path,
					is_dir = resource["is_dir"],
					uid = resource_stat.st_uid,
					gid = resource_stat.st_gid,
					mode = resource["mode"],
					size = str(resource_stat.st_size / 1024)+"mb",
					atime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(resource_stat.st_atime)),
					mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(resource_stat.st_mtime)))
			self.window.run_command(
					cmd="ssh_panel_output",
					args={
						"content": html_tmp(content=html_ele),
						"is_html": True,
						"new_line": False,
						"clean": True
					}
				)
		def resource_delete(id):
			resource = self.resource_data[id]
			resource_path = self.path_by_resource(resource)
			def confirm():
				if resource["is_dir"]:
					try:
						self.client.sftp_client.rmdir(resource_path)
					except Exception as e:
						self.focus_tip = icon_style["denied"]
						LOG.E("rmdir %s Falied,please check permission and the directory empty,see [info]"%resource_path)
				else:
					self.client.sftp_client.remove(resource_path)
				del self.resource_data[id]
				self.update_view_port()
				sublime.status_message("deleted %s"%resource_path)
			self.window.show_quick_panel(
				["confirm deletion %s"%resource_path,"cancel"],
				lambda i: confirm() if i==0 else None,
				sublime.KEEP_OPEN_ON_FOCUS_LOST|sublime.MONOSPACE_FONT
			)
		def resource_click(id):
			resource_data = self.resource_data
			resource = resource_data[id]
			resource["focus"] = not resource["focus"]
			resource_path = self.path_by_resource(resource)
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
							self.add_path(resource_path,root_path=self.path_by_resource(resource))
					else:
						self.clean_resource(resource)
			else:
				self.open_resource_file(resource)
			self.update_view_port()
		def resource_menu(id):
			operation_menu = [
				("show info",resource_info),
				("delete",resource_delete)
			]
			if self.resource_data[id]["is_dir"]:
				operation_menu.extend([
					("add file",resource_create_file),
					("add directory",resource_create_dir),
					("clone directory",resource_clone_dir)
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
		with async_Lock:
			# if operation in available_operation:
			eval("{operation}('{args}')".format(operation=operation,args=args))

	def open_resource_file(self,resource):
		remote_path = self.path_by_resource(resource)
		global path_hash_map
		remote_os_sep = self.client.remote_os_sep
		path_hash,local_path_root,_ = path_hash_map.get(resource["root_path"])
		save_hash_root = os.path.sep.join([local_path_root,path_hash]) # local_path_root/path_hash
		if resource["root_path"] == "/":
			local_path = save_hash_root + os.path.sep.join(remote_path.split(remote_os_sep))
		else:
			local_path = save_hash_root + os.path.sep.join(remote_path.replace(resource["root_path"],"",1).split(remote_os_sep)) # local_path_root/path_hash/remote_mapping_path
		LOG.D("path_hash_map",path_hash_map)
		if (not self.window.open_file(local_path,sublime.TRANSIENT).is_dirty()) or (not os.path.exists(local_path)):
			os.makedirs(os.path.split(local_path)[0], exist_ok=True)
			@async_run
			def fn():
				self.client.file_sync(local_path,remote_path,dir="get",sync_stat=True)
				self.window.open_file(local_path,sublime.TRANSIENT)
			try:
				fn()
			except Exception as e:
				self.focus_tip = icon_style["error"]
				self.update_view_port()
				LOG.E("file sync failed",{
					"remote_path":remote_path,
					"local_path": local_path,
					"error": str(e.args)
				})

	def add_root_path(self,path,focus=False):
		id = self._new_resource_id()
		global path_hash_map
		fs = self.client.sftp_client.lstat(path)
		resource = {
			"name": path,
			"mode": oct(stat.S_IMODE(fs.st_mode)).replace("0o",""),
			"access": accessable(fs,*(self.client.userid)),
			"is_dir": True,
			"expand": False,
			"focus": focus,
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
			{hostname}<span class='symbol'>@{username}</span>
			<p>
				<a href="show:info">[i]</a>
				<a href="reload:list">[R]</a>
				<a href="edit_settings:' '">[E]</a>
				<a href="run_command:' '">[T]</a>
				<a href="show_panel:' '">[P]</a>
				<a href="add_root_path:' '">[+]</a>
				<a href="show:help">[?]</a>
			</p>
		</p>
		{dirtory_tree}
		'''.format(
				hostname=self.client.user_settings_config["hostname"] if self.client else self.user_settings.config["hostname"],
				username=self.user_settings.config["username"],
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
				self.path_by_resource(self.focus_resource) if self.focus_resource else self.user_settings.server_name if self.client else "connect lost"
			))
		if "SSH-Panel.hidden-color-scheme" not in nv.settings().get("color_scheme"):
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
			theme_resource = self.save_theme({
				"globals":new_style_global,
				"variables":{
				},
				"name":"SSH-Panel"
				})
			nv.settings().set("color_scheme",theme_resource)
		self.phantom_items = [phantom]
		self.update_phantom()
		# LOG.D("resource_data",self.resource_data)

	def update_phantom(self):
		self.PhantomSet.update(self.phantom_items)

	def path_by_resource(self,resource,dir_sep=False):
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

	def render_resource_list(self):
		if self.client == None:
			return "<a href='reload:connect'>no connect</a>"
		ele_list = []
		os_sep_symbol = "<span class='symbol'>%s</span>"%self.client.remote_os_sep if icon_style.get("dir_symbol") else ""
		# os_sep_symbol = ""
		for resource_id,resource in self.resource_data.items():
			resource_path = self.path_by_resource(resource)
			ext = os.path.splitext(resource["name"])[1][1:]
			ele = "<p style='padding-left:{depth}px'>{file_icon}<a class='{style_class}' href='resource_click:{resource_id}'>{text}</a>{symbol}{focus_tip}<span class='operation_menu'>{operation_menu}</span></p>".format(
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
					focus_tip = self.focus_tip if resource["focus"] else ""
				)
			ele_list.append(ele)
		id_re_rule = re.compile(r"(?<=resource_click:)\d+")
		def get_resource_path(ele):
			id = id_re_rule.search(ele).group()
			resource = self.resource_data[id]
			resource_path = self.path_by_resource(resource,dir_sep=True)
			if resource["root_path"] == "":
				return resource_path
			else:
				return resource["root_path"] + self.client.remote_os_sep + resource_path
		ele_list.sort(key = get_resource_path)
		return "".join(ele_list)

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