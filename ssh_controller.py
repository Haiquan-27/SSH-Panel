import sublime
import sublime_plugin
import paramiko
import importlib
import util
importlib.reload(util)
from util import *
import os
import stat
import time
import re
import sys


settings_name = "ssh-panel.sublime-settings"

AUTH_METHOD_PASSWORD = 0	# 0: username and password	
AUTH_METHOD_PRIVATEKEY = 1	# 1: username and private_key	
AUTH_METHOD_GSSAPI = 2		# 2: username and gssapi	

def plugin_loaded():
	st_settings = sublime.load_settings(settings_name)
	global DEBUG
	DEBUG = st_settings.get("debug_mode")

LOG = SSHPanelLog()

class UserSettings():
	def __init__(self):
		self.server_name = None
		self.auth_parameter = None
		self.connect_parameter = None
		self.auth_method = None

	def init_from_settings_file(self,server_name):
		st_settings = sublime.load_settings(settings_name)
		user_parameter = st_settings.get("server_settings")[server_name]
		default_parameter = st_settings.get("default_connect_settings")
		self.auth_parameter,self.connect_parameter,self.auth_method = UserSettings.format_parameter(default_parameter,user_parameter)
		if ((self.auth_parameter,self.connect_parameter,self.auth_method) == ({},{},None) or
			UserSettings.check_config_error(self.config,self.auth_method) != []):
				LOG.E("%s settings parameter error, please see ssh-panel.sublime-settings\nerror parameter:"%server_name,
					UserSettings.check_config_error(self.config,self.auth_method))
		self.server_name = server_name

	def init_from_parameter(self,server_name,parameter):
		self.server_name = server_name
		self.auth_parameter,\
		self.connect_parameter,\
		self.auth_method = UserSettings.format_parameter(
			sublime.load_settings(settings_name).get("default_connect_settings"),
			parameter)
		if ((self.auth_parameter,self.connect_parameter,self.auth_method) == ({},{},None) or
			UserSettings.check_config_error(self.config,self.auth_method) != []):
				LOG.E("%s settings parameter error, please see ssh-panel.sublime-settings\nerror parameter:"%server_name,
					UserSettings.check_config_error(self.config,self.auth_method))

	@classmethod
	def format_parameter(cls,default_parameter,user_parameter):
		default_parameter["remote_path"] = default_parameter.get("remote_path","$HOME/")
		default_parameter["local_path"] = default_parameter.get("local_path",os.sep.join([os.path.expanduser('~'),"SFTP-Local","{auto_generate}"]))
		default_parameter["network_timeout"] = default_parameter.get("network_timeout",20)
		default_parameter["port"] = default_parameter.get("port",22)
		default_parameter["known_hosts_file"] = default_parameter.get("known_hosts_file","")
		auth_parameter = {}
		connect_parameter = {}
		if (user_parameter.get("username",None) and
			user_parameter.get("password",None) and
			user_parameter.get("hostname",None)
			):
			auth_parameter = {
				"username":user_parameter.get("username"),
				"hostname":user_parameter.get("hostname"),
				"password":user_parameter.get("password"),
				"save_password":user_parameter.get("save_password",True)
			}
			auth_method = AUTH_METHOD_PASSWORD
		elif (user_parameter.get("username",None) and 
			user_parameter.get("hostname",None) and
			user_parameter.get("private_key",None) and
			len(user_parameter.get("private_key")) == 2 and
			user_parameter.get("private_key")[0] in ["RSAKey","DSSKey","ECDSAKey","Ed25519Key"]
			):
			private_key = user_parameter.get("private_key")
			private_key[1] = os.path.expandvars(private_key[1])
			auth_parameter = {
				"username":user_parameter.get("username"),
				"hostname":user_parameter.get("hostname"),
				"private_key":private_key,
				"need_passphrase":user_parameter.get("need_passphrase",False)
			}
			auth_method = AUTH_METHOD_PRIVATEKEY
		elif(user_parameter.get("username",None) and 
			user_parameter.get("gss_host",None) and
			user_parameter.get("gss_auth",None) and
			user_parameter.get("gss_kex",None) and
			user_parameter.get("gss_deleg_creds",None) and
			user_parameter.get("gss_trust_dns",None)):
			auth_parameter = {
				"username":user_parameter.get("username"),
				"gss_host":user_parameter.get("gss_host"),
				"gss_auth":user_parameter.get("gss_auth"),
				"gss_kex":user_parameter.get("gss_kex"),
				"gss_deleg_creds":user_parameter.get("gss_deleg_creds"),
				"gss_trust_dns":user_parameter.get("gss_trust_dns")
			}
			auth_method = AUTH_METHOD_GSSAPI
		else:
			return ({},{},None)
		for s in default_parameter.keys():
			connect_parameter[s] = user_parameter.get(s,default_parameter[s])

		connect_parameter["known_hosts_file"] = os.path.expandvars(connect_parameter["known_hosts_file"])

		return (
				auth_parameter,
				connect_parameter,
				auth_method
				)

	@classmethod
	def check_config_error(cls,config,auth_method):
		error_list = []
		if config==None or auth_method==None:
			LOG.E("parameter parse failed please, possible causes following:",
				[
					"your missing requisite parameter",
					"incorrect parameter type",
					"please to edit_settings check your settings</a>",
				])
		if not isinstance(config["remote_path"],str):error_list.append("remote_path")
		if not isinstance(config["local_path"],str):error_list.append("local_path")
		# if not (os.path.exists(os.path.expandvars(config["local_path"])) or "{auto_generate}" in config["local_path"]):
		# 	error_list.append("local_path")
		if not isinstance(config["network_timeout"],int):error_list.append("network_timeout")
		if not (isinstance(config["port"],int)):error_list.append("port")
		if (not os.path.exists(os.path.expandvars(config["known_hosts_file"])) and config["known_hosts_file"] != ""):
			error_list.append("known_hosts_file")
		#  os.path.exists(os.path.expandvars(user_parameter.get("private_key")[1]))
		if auth_method == AUTH_METHOD_PASSWORD:
			if not isinstance(config["username"],str):error_list.append("username")
			if not isinstance(config["password"],str):error_list.append("password")
			if not isinstance(config["hostname"],str):error_list.append("hostname")
			if not isinstance(config["save_password"],bool):error_list.append("save_password")
		elif auth_method == AUTH_METHOD_PRIVATEKEY:
			if not isinstance(config["username"],str):error_list.append("username")
			if not isinstance(config["hostname"],str):error_list.append("hostname")
			if (not isinstance(config["private_key"],list) or
					config["private_key"][0] not in ["RSAKey","DSSKey","ECDSAKey","Ed25519Key"] or
					not os.path.exists(os.path.expandvars(config["private_key"][1]))):
				error_list.append("private_key")
			if not isinstance(config["need_passphrase"],bool):error_list.append("need_passphrase")
		elif auth_method == AUTH_METHOD_GSSAPI:
			if not isinstance(config["username"],str):error_list.append("username")
			if not isinstance(config["gss_host"],str):error_list.append("gss_host")
			if not isinstance(config["gss_auth"],bool):error_list.append("gss_auth")
			if not isinstance(config["gss_kex"],bool):error_list.append("gss_kex")
			if not isinstance(config["gss_deleg_creds"],bool):error_list.append("gss_deleg_creds")
			if not isinstance(config["gss_trust_dns"],bool):error_list.append("gss_trust_dns")
		return error_list

	@classmethod
	def to_config(cls,auth_parameter,connect_parameter,auth_method=None):
		try:
			all_config = dict(auth_parameter,**connect_parameter)
			if all_config.get("save_password") == False:
				all_config["password"] = ""
			return all_config
		except TypeError:
			LOG.E("UserSettings has not init",{
					"server_name": self.server_name,
					"auth_parameter": self.auth_parameter,
					"connect_parameter": self.connect_parameter,
					"auth_method": self.auth_method
				})

	@property
	def config(self):
		return UserSettings.to_config(self.auth_parameter,self.connect_parameter)

	def save_config(self):
		server_name = self.server_name
		save_config = self.config # 没初始化会报错
		if server_name and save_config:
			st_settings = sublime.load_settings(settings_name)
			server_settings = st_settings.get("server_settings")
			default_parameter = st_settings.get("default_connect_settings")
			for s in default_parameter.keys(): # 查重
				if save_config[s] == default_parameter[s]:
					del save_config[s]
			server_settings[server_name] = save_config
			st_settings.set("server_settings",server_settings)
		sublime.save_settings(settings_name)

	def delete_from_settings_file(cls,server_name):
		st_settings = sublime.load_settings(settings_name)
		server_settings = st_settings.get("server_settings")
		del server_settings[server_name]
		st_settings.set("server_settings",server_settings)
		subilme.save_settings(settings_name)


class ClientObj():
	def __init__(
				self,
				user_settings, # UserSettings
				):
		self._user_settings = user_settings
		self.user_settings_config = user_settings.config
		self.user_settings = self._user_settings
		self.transport = None
		self.sftp_client = None
		self.remote_platform = "unknown"
		self.env = None
	@property
	def user_settings(self):
		return self._user_settings

	@user_settings.setter
	def user_settings(self,value):
		self._user_settings = value
		self.user_settings_config = value.config
		user_settings_config = self.user_settings_config
		# 自动生成 local_path
		while(user_settings_config["local_path"].find("{auto_generate}") > -1): # 使用auto_generate,将返回由当前参数、字符索引数、时间戳生成的md5值
			user_settings_config["local_path"] = user_settings_config["local_path"].replace(
				"{auto_generate}",
				hashlib.md5(
					(
						str(user_settings_config) +
						str(user_settings_config["local_path"].find("{auto_generate}")) +
						str(time.time())
					).encode("utf8")
					).hexdigest(),
				1
			)
		# 转为绝对路径，转换其中的变量
		user_settings_config["local_path"] = os.path.expandvars(user_settings_config["local_path"])
		user_settings_config["known_hosts_file"] = os.path.expandvars(user_settings_config["known_hosts_file"])
		self._user_settings.init_from_parameter(
			self._user_settings.server_name,
			user_settings_config
		)

	def connect(self):
		user_settings = self.user_settings
		user_settings_config = user_settings.config
		transport_parameter = {}
		hostname,port = (None,user_settings_config["port"])
		def try_connect():
			start_time = time.time()
			try:
				transport = paramiko.Transport(sock=(hostname,port))
			except paramiko.ssh_exception.SSHException as e:
				LOG.E("Connect failed",{
					"Error":e.args,
					"timeuse":time.time() -  start_time
					})

			known_hosts_file = user_settings_config["known_hosts_file"]
			try:
				transport.connect(**transport_parameter)
			except paramiko.ssh_exception.AuthenticationException as e:
				LOG.E("Authentication failed.:%s"%(e.args),self.user_settings_config)
			server_key = transport.get_remote_server_key()

			kh_kex = None # 远程主机公钥加密算法
			kh_key = None # 远程主机公钥
			if known_hosts_file != "": # 使用known_hosts中的认证方式和远程主机公钥
				try :
					kh_data = paramiko.HostKeys(known_hosts_file).lookup(hostname)
				except IOError:
					LOG.E("%s file open error or not exists, please to check"%known_hosts_file)
				if kh_data:
					kh_kex = kh_data.keys()[0]
					kh_key = kh_data[kh_kex]
					transport_parameter["hostkey"] = kh_key
				else:
					LOG.W("host no such in known_hosts,please confirm whether you trust this host",
							{
								"hostname":hostname,
								"key_name":server_key.get_name(),
								"fingerprint": abstract("sha256",server_key.asbytes()) + " (%s,%s)"%("sha256","base64")
								# ssh-keyscan -t [kh_kex] [host_name] | awk '{print $3}' |base64 -d|openssl [abstract_algorithm_name] -binary |base64
							}
						)
					if sublime.yes_no_cancel_dialog(
						"Are you sure you want to continue connecting (yes/no)?"
						,"yes","no"):
						pass
					else:
						LOG.I("user clean")
						return
			LOG.I("Authentication Successful")
			self.transport = transport
			channel = self.get_new_channel()
			channel.invoke_subsystem('sftp')
			self.sftp_client =  paramiko.SFTPClient(sock=channel)
			test_platform = self.get_platform()
			self.remote_platform = test_platform if test_platform else "unknown"
			self.env = self.get_env()
			self.user_settings_config["remote_path"] = self.remote_expandvars(self.user_settings_config["remote_path"])
			LOG.I("Connect Successful","time use:%s"%(time.time() - start_time))
			self.user_settings.save_config()
			LOG.D("Configure has saved",self.user_settings_config)
		if user_settings.auth_method == AUTH_METHOD_PASSWORD:
			transport_parameter = {
				"username": user_settings_config["username"],
				"password": user_settings_config["password"]
			}
			hostname = user_settings_config["hostname"]
			try_connect()
		elif user_settings.auth_method == AUTH_METHOD_PRIVATEKEY:
			pkey = None
			pkey_kex = user_settings_config["private_key"][0]
			pkey_file = os.path.expandvars(user_settings_config["private_key"][1])
			# paramiko.[RSAKey/DSSKey/ECDSAKey/Ed25519Key].from_private_key_file()
			passphrase = user_settings_config["private_key"]
			hostname = user_settings_config["hostname"]
			transport_parameter = {
				"username": user_settings_config["username"],
				"pkey": pkey
			}
			if user_settings_config["need_passphrase"]:
				def on_done(input):
					transport_parameter["pkey"] = eval("paramiko.%s"%pkey_kex).from_private_key_file(pkey_file,password=input)
					try_connect()
				sublime.active_window().show_input_panel(
						"passshrase:",
						"",
						on_done,None,None
					)
			else:
				transport_parameter["pkey"] = eval("paramiko.%s"%pkey_kex).from_private_key_file(pkey_file)
				try_connect()
		elif user_settings.auth_method == AUTH_METHOD_GSSAPI:
			transport_parameter = {
				"username":user_settings_config["username"],
				"gss_host":user_settings_config["gss_host"],
				"gss_auth":user_settings_config["gss_auth"],
				"gss_kex":user_settings_config["gss_kex"],
				"gss_deleg_creds":user_settings_config["gss_deleg_creds"],
				"gss_trust_dns":user_settings_config["gss_trust_dns"]
			}
			hostname = user_settings_config["gss_host"] # 不确定
			try_connect()

	@property
	def remote_os_sep(self):
		return "\\" if self.remote_platform == "windows" else "/"

	def get_new_channel(self):
		chan = self.transport.open_session(timeout=self.user_settings_config["network_timeout"]) # 设置打开session的timeout
		chan.settimeout = self.user_settings_config["network_timeout"] # 交互timeout
		return chan

	def exec_command(self,command):
		chan = self.get_new_channel()
		chan.exec_command(command)
		stdin = chan.makefile_stdin("wb", -1)
		stdout = chan.makefile("r", -1)
		stderr = chan.makefile_stderr("r", -1)
		return {
			"stdin" :stdin,
			"stdout":stdout,
			"stderr":stderr
		}

	def get_env(self):
		cmd = "env"
		if self.remote_platform == "windows":
			cmd = "set"
		cmd_res = self.exec_command(cmd).get("stdout").read().decode("utf8")
		cmd_res = cmd_res.replace("\r\n","\n")
		env = {}
		for l in cmd_res.split("\n"):
			if l != "":
				name = l[:l.index("=")]
				value = l[l.index("=")+1:]
				env[name] = value
		return env

	def get_platform(self):
		test_cmd = "echo ~"
		cmd_res = self.exec_command(test_cmd).get("stdout").read().decode("utf8")
		if cmd_res[0] == "/":
			remote_platform = "like-linux"
		elif cmd_res[0] == "~":
			remote_platform = "windows"
		return remote_platform

	def remote_expandvars(self,path):
		re_rule = None
		env_symbol = ""
		if self.remote_platform == "windows":
			re_rule = re.compile(r"%.*?%")
			env_symbol = "%"
		else:
			re_rule = re.compile(r"\$[a-zA-z_]+")
			env_symbol = "$"
		if re_rule.match(path) == None:
			return path
		remote_env = self.env if self.env else self.get_env()
		def env_replace(match):
			env_str = match.group()
			env_name = env_str.replace(env_symbol,"")
			return remote_env.get(env_name,env_str)
		remote_path = re_rule.sub(env_replace,path)
		if remote_path[-1] == self.remote_os_sep:
			remote_path = remote_path[:-1]
		return remote_path

	def local_path_mapping(self,remote_path): # 远程路径转为本地路径
		remote_path_base = self.user_settings_config["remote_path"]
		local_path_base = self.user_settings_config["local_path"]
		if local_path_base[-1] == os.sep:
			local_path_base[-1] = local_path_base[:-1]
		if remote_path.find(remote_path_base) == 0:
			remote_path = remote_path.replace(remote_path_base,"")
		else:
			return
		local_path = local_path_base + os.sep.join(remote_path.split(self.remote_os_sep))
		return local_path

	def remote_path_mapping(self,local_path): # 本地路径转为远程路径
		# 转化路径格式
		remote_path_base = self.user_settings_config["remote_path"]
		local_path_base = self.user_settings_config["local_path"]
		if remote_path_base[-1] == self.remote_os_sep:
			remote_path_base = remote_path_base[:-1]
		if local_path.find(local_path_base) == 0:
			local_path = local_path.replace(local_path_base,"")
		else:
			return
		remote_path = remote_path_base + self.remote_os_sep.join(local_path.split(os.sep))
		return remote_path

	def disconnect(self):
		LOG.I(self.user_settings.server_name+" close")
		self.sftp_client.close()

	def get_dir_list(self,remote_path="."):
		res = []
		remote_path = self.remote_expandvars(remote_path)
		for fs in self.sftp_client.listdir_iter(remote_path):
			fs_item = {}
			fs_item["file_name"] = fs.filename
			fs_item["mode"] = oct(stat.S_IMODE(fs.st_mode)).replace("0o","")
			fs_item["is_dir"] = stat.S_ISDIR(fs.st_mode)
			# fs_item["u"] =
			# fs_item["g"] =
			# fs_item["size"] =
			res.append(fs_item)
		return res

	def file_sync(self,local_path,remote_path,dir,sync_stat=False): # 写入并保持远程文件原始权限
		# remote_path = ssh_file.remote_path
		# local_path = ssh_file.local_path
		try:
			if dir == "put":
				with self.sftp_client.open(remote_path,"w") as rf:
					with open(local_path,"rb") as lf:
						rf.write(lf.read())
				if sync_stat:
					local_stat = os.stat(local_path)
					local_atime = local_stat.st_atime
					local_mtime = local_stat.st_mtime
					self.sftp_client.utime(remote_path,(local_atime,local_mtime))
					self.sftp_client.chmod(remote_path,stat.S_IMODE(local_stat.st_mode))
				LOG.D("remote:%s sync"%remote_path)
			elif dir == "get":
				os.makedirs(os.path.split(local_path)[1],exist_ok=True)
				with open(local_path,"wb") as lf:
					with self.sftp_client.open(remote_path,"rb") as rf:
						lf.write(rf.read())
				if sync_stat:
					remote_stat = self.sftp_client.stat(remote_path)
					remote_atime = remote_stat.st_atime
					remote_mtime = remote_stat.st_mtime
					os.utime(local_path,(remote_atime,remote_mtime))
					os.chmod(local_path,stat.S_IMODE(remote_stat.st_mode))
				LOG.D("local:%s sync"%local_path)
		except PermissionError as e:
			LOG.E("file %s writing Failed:%s"%(remote_path,e),{
					"local_path":local_path,
					"remote_path":remote_path
				})

	# save_host_keys


