import sublime
import sublime_plugin
import os
import json
import re
import time

import importlib # debug
import ssh_controller # debug
importlib.reload(ssh_controller) # debug
from ssh_controller import *
import util # debug
importlib.reload(util) # debug
from util import *


client_mapping = {}
_max_client_id = -1
def register_client(client):
	global client_mapping
	global _max_client_id
	_max_client_id += 1
	new_id = str(_max_client_id)
	client_mapping[new_id] = client
	return new_id
def update_client(id,client):
	global client_mapping
	client_mapping[id] = client


def plugin_loaded():
	pass

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
		self.show_penel()

	def show_penel(self,start_index=0):
		show_item_list = []
		server_config_data_items = list(self.user_config_data.items())
		default_settings = sublime.load_settings(settings_name).get("default_connect_settings")
		for server_name,(user_config,auth_method) in server_config_data_items:
			show_item_list.append([server_name,user_config["remote_path"]])

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
					"from_settings":True
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


class SshPanelCreateConnectCommand(sublime_plugin.WindowCommand):
	def __init__(self,window):
		super().__init__(window)
		self.PhantomSet = None # phantom 管理器
		self.phantom_items = []
		self.client = None
		self.client_id = None
		self.resource_data = None
		self._max_resource_id = 0
		self._user_settings = None
		self.focus_resource = None
		self.navcation_view = None
		self.root_path_list = []

	def run(self,
		server_name: str,
		connect_now: bool,
		from_settings: bool=True,
		server_parameter: dict=None, # 如果设置了from_settings=False则必须设置
		# ...
		):
		self.resource_data = {}
		self._max_resource_id = -1
		self.focus_resource = None
		if sublime.load_settings(settings_name).get("new_window",True):
			sublime.active_window().run_command("new_window")
			window = sublime.windows()[-1]
			window.set_sidebar_visible(False)
			self.window = window
		split_layout = {
			'cells': [
					[0, 0, 1, 1],
					[1, 0, 2, 1]
				],
			'cols': [0.0, 0.2, 1.0],
			'rows': [0.0, 1.0]
		}
		window.set_layout(split_layout)
		navication_view = window.new_file()
		window.set_view_index(navication_view,0,0)
		window.focus_group(1)
		user_settings = UserSettings()
		if from_settings:
			user_settings.init_from_settings_file(server_name)
		else:
			user_settings.init_from_parameter(server_name,server_parameter)
		self.user_settings = user_settings
		self.init_navcation_view(navication_view)
		self.navication_view = navication_view
		if connect_now:
			self.connect_post(user_settings)

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
			# self.add_path(client.user_settings_config["remote_path"])
			self.new_main_resource(path=self.client.user_settings_config["remote_path"],focus=True)
			self.update_view_port()
			LOG.D("OS ENV",self.client.env)
			if self.client.get_platform() == "windows":
				self.interattach = self.client.exec_command(r"C:\Windows\System32\cmd.exe")
				LOG.D("Shell","cmd.exe")
			else:
				self.interattach = self.client.exec_command("/bin/sh")
				LOG.D("Shell","bash")

	def reload_list(self):
		self._max_resource_id = -1
		self.resource_data = {}
		if self.client:
			# self.add_path(self.client.user_settings_config["remote_path"])
			self.new_main_resource(path=self.client.user_settings_config["remote_path"],focus=True)
		self.update_view_port()

	def add_path(self,remote_path,root_path):
		resource_data = self.resource_data
		res = []
		# 使用self.client.get_dir_list会执行两次循环
		for fs in self.client.sftp_client.listdir_iter(remote_path):
			resource_item = {}
			resource_item["name"] = fs.filename
			resource_item["mode"] = oct(stat.S_IMODE(fs.st_mode)).replace("0o","")
			resource_item["is_dir"] = stat.S_ISDIR(fs.st_mode)
			resource_item["root_path"] = root_path
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

	def _new_resource_id(self):
		self._max_resource_id += 1
		return str(self._max_resource_id)

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
					<p><span class='keyword'>[I] </span>show server infomation<p>
					<p><span class='keyword'>[R] </span>refresh ans sync file list<p>
					<p><span class='keyword'>[E] </span>edit settings<p>
					<p><span class='keyword'>[?] </span>help<p>
				"""
					# <p><span class='keyword'>[+] </span>add new main list <span class='warning'>(Under development | Not recommended)</span><p>
				self.window.run_command(
					cmd="ssh_panel_output",
					args={
						"content": html_tmp(content=html_ele),
						"is_html": True,
						"new_line": False,
						"clean": True
					}
				)
		def new_main_resource(_):
			def on_done(path):
				if self.client and path != self.client.user_settings_config["remote_path"]:
					self.new_main_resource(path=path,focus=True)
					self.update_view_port()
			self.window.show_input_panel(
				"add path:",
				"",
				on_done,
				None,
				None)
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
					LOG.E("interattach failed",e.args)
			self.window.show_input_panel(
				"cmd:",
				"",
				on_done,
				None,
				None)
		def edit_settings(_):
			self.window.run_command(
					cmd = "edit_settings",
					args = {
					  "base_file": "${packages}/SSH-Panel/ssh-panel.sublime-settings",
					  "default": """
{
	"server_settings":{
		"MyServer":{
			"username":"",
			"remote_path": "$HOME",
			"local_path": "",
			"hostname":"",
			"password":"",
			"save_password":true,
		},
	}
}"""
					})
		def resource_create_file(id):
			resource = self.resource_data[id]
			resource_path = self.path_by_resource(resource)
			def on_done(path):
				if path[-1] == self.client.remote_os_sep: return
				path = self.client.remote_expandvars(path)
				f =  self.client.sftp_client.open(path,"a")
				f.close()
				id = self._new_resource_id()
				new_resource = {
					"name": os.path.split(path)[-1],
					"mode": oct(stat.S_IMODE(self.client.sftp_client.lstat(path).st_mode)).replace("0o",""),
					"is_dir": False,
					"focus": False,
					"root_path": resource["root_path"] if resource["root_path"] != "" else self.path_by_resource(resource),
					"where": os.path.split(path)[0],
					"depth": self.focus_resource["depth"] + 1
				}
				self.resource_data[id] = new_resource
				self.update_view_port()
				sublime.status_message("create %s"%self.path_by_resource(new_resource))
			self.window.show_input_panel(
				"new file:",
				resource_path+self.client.remote_os_sep,
				on_done,
				None,
				None)
		def resource_create_dir(id):
			resource = self.resource_data[id]
			resource_path = self.path_by_resource(resource)
			def on_done(path):
				if path[-1] == self.client.remote_os_sep:
					path = path[:-1]
				path = self.client.remote_expandvars(path)
				id = self._new_resource_id()
				self.client.sftp_client.mkdir(path)
				new_resource = {
					"name": os.path.split(path)[-1],
					"mode": oct(stat.S_IMODE(self.client.sftp_client.lstat(path).st_mode)).replace("0o",""),
					"is_dir": True,
					"expand": False,
					"focus": False,
					"root_path": resource["root_path"] if resource["root_path"] != "" else self.path_by_resource(resource),
					"where": os.path.split(path)[0],
					"depth": self.focus_resource["depth"] + 1
				}
				self.resource_data[id] = new_resource
				self.update_view_port()
				sublime.status_message("create %s"%self.path_by_resource(new_resource))
			self.window.show_input_panel(
				"new dir:",
				resource_path+self.client.remote_os_sep,
				on_done,
				None,
				None)
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
			resource = self.resource_data[id]
			resource["focus"] = not resource["focus"]
			resource_path = self.path_by_resource(resource)
			if resource["focus"]:
				if self.focus_resource and self.focus_resource != resource: # 是否取消上一次的焦点
					self.focus_resource["focus"] = False
				self.focus_resource = resource
			if resource["is_dir"]:
				if resource["focus"] and resource["expand"]: # 另外点击一个展开的无焦点目录，给予焦点且保持展开
					resource["focus"] = True
				else:
					resource["expand"] = not resource["expand"]
					if resource["expand"]:
						if resource["root_path"] != "": # 始终继承父级的root_path
							self.add_path(resource_path,root_path=resource["root_path"])
						else:
							self.add_path(resource_path,root_path=self.path_by_resource(resource))
					else: # 删除非展开目录下的资源
						for id,path_where in [(id,self.resource_data[id]["where"]) for id in self.resource_data.keys()]:
							if path_where.startswith(resource_path):
								del self.resource_data[id]
			else:
				self.open_resource_file(resource)
			self.update_view_port()
		def resource_menu(id):
			operation_menu = [
				("show info",resource_info),
				("delete",resource_delete)
			]
			if self.resource_data[id]["is_dir"]:
			# 	operation_menu += """
			# 	<p><a href='resource_create_file:{id}'>add file</a></p>
			# 	<p><a href='resource_create_dir:{id}'>add directory</a></p>
			# 	""".format(id=id)
				operation_menu.extend([
					("add file",resource_create_file),
					("add directory",resource_create_dir)
				])
			# self.navication_view.show_popup(
			# 	html_tmp(content=operation_menu),
			# 	sublime.HIDE_ON_MOUSE_MOVE_AWAY,
			# 	0,300,300,
			# 	self.navcation_href_click,None
			# )
			if int(sublime.version()) >= 4081:
				self.window.show_quick_panel(
					[d[0] for d in operation_menu],
					lambda i: operation_menu[i][1](id) if i!=-1 else None,
					sublime.KEEP_OPEN_ON_FOCUS_LOST|sublime.MONOSPACE_FONT,
					placeholder = "you can"
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
		local_path = self.client.local_path_mapping(remote_path)
		if (not self.window.open_file(local_path,sublime.TRANSIENT).is_dirty()) or (not os.path.exists(local_path)):
			os.makedirs(self.client.local_path_mapping(resource["where"]), exist_ok=True)
			@async_run
			def fn():
				self.client.file_sync(local_path,remote_path,dir="get",sync_stat=True)
				self.window.open_file(local_path,sublime.TRANSIENT)
			fn()

	def new_main_resource(self,path,focus=False):
		id = self._new_resource_id()
		resource = {
			"name": path,
			"mode": oct(stat.S_IMODE(self.client.sftp_client.lstat(path).st_mode)).replace("0o",""),
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
		if path not in self.root_path_list:
			self.root_path_list.append(path)

	def update_view_port(self):
		html_ele = '''
		<p class="title_bar">
			{hostname}<span class='symbol'>@{username}</span>
			<p>
				<a href="show:info">[i]</a>
				<a href="reload:list">[R]</a>
				<a href="edit_settings:' '">[E]</a>
				<a href="run_command:' '">[T]</a>
				<a href="show:help">[?]</a>
			</p>
		</p>
		{dirtory_tree}
		'''.format(
				hostname=self.client.user_settings_config["hostname"] if self.client else self.user_settings.config["hostname"],
				username=self.user_settings.config["username"],
				dirtory_tree=self.render_resource_list()
			)
				# <a href="new_main_resource:' '">[+]</a>
		phantom = sublime.Phantom(
			sublime.Region(0),
			html_tmp(content=html_ele),
			sublime.LAYOUT_INLINE,
			on_navigate=self.navcation_href_click)
		nv = self.navication_view
		nv.set_name("%s|%s"%(
			self.user_settings.server_name,
			self.client.user_settings_config["hostname"] if self.client else self.user_settings.config["hostname"]))
		if nv.settings().get("color_scheme").find("SSH-Panel.hidden-color-scheme") == -1:
			src_style = nv.style()
			new_style_global = {}
			src_background_color = ""
			theme_dark_color = int(src_style.get("background").replace("#","0x"),16)
			theme_dark_color -= 0x101010
			theme_dark_color &= 0xffffff
			theme_dark_color = hex(theme_dark_color).replace("0x","#")
			new_style_global["background"] = theme_dark_color
			new_style_global["foreground"] = src_style["foreground"]
			theme_resource = self.save_theme({
				"globals":new_style_global,
				"variables":{
				},
				"name":"SSH-Panel"
				})
			nv.settings().set("color_scheme",theme_resource)
		self.phantom_items = [phantom]
		self.update_phantom()
		LOG.D("resource_data",self.resource_data)

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
		return path

	def render_resource_list(self):
		if self.client == None:
			return "<a href='reload:connect'>no connect</a>"
		ele_list = []
		os_sep_symbol = "<span class='symbol'>%s</span>"%self.client.remote_os_sep
		for resource_id,resource in self.resource_data.items():
			resource_path = self.path_by_resource(resource)
			ele = "<p style='padding-left:{depth}px'><a class='{style_class}' href='resource_click:{resource_id}'>{text}</a>{symbol}<span class='operation_menu'>{operation_menu}</span></p>".format(
					style_class = "res_focus" if resource["focus"] else "res",
					resource_id = resource_id,
					depth = resource["depth"] * 30,
					text = (resource["name"]).
								replace("&","&amp;").
								replace("<","&lt;").
								replace(">","&gt;").
								replace(" ","&nbsp;"),
					symbol = os_sep_symbol if resource["is_dir"] else "",
					operation_menu = "<a href='resource_menu:%s'>[...]</a>"%resource_id if resource["focus"] else ""
				)
			ele_list.append(ele)
		# for id in ignore_id_list:
		# 	del self.resource_data[id]
		id_re_rule = re.compile(r"(?<=resource_click:)\d+")
		def get_resource_path(ele):
			id = id_re_rule.search(ele).group()
			resource_path = self.path_by_resource(self.resource_data[id],dir_sep=True)
			return resource_path
		ele_list.sort(key = get_resource_path)
		return "".join(ele_list)

class SshPanelEventCommand(sublime_plugin.ViewEventListener):
	@classmethod
	def is_applicable(self,settings):
		return client_mapping != {}

	def on_post_save_async(self):
		file_name = self.view.file_name()
		for client_id,client in client_mapping.items():
			if file_name.startswith(client.user_settings_config["local_path"]):
				client.file_sync(
					file_name,
					client.remote_path_mapping(file_name),
					"put",
					sync_stat=True)

	def on_close(self):
		client_id = self.view.settings().get("ssh_panel_clientID",None)
		if client_id:
			global client_mapping
			client = client_mapping[client_id]
			client.disconnect()
			del client_mapping[client_id]
