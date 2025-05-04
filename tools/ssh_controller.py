import sublime
import sublime_plugin
from .util import *
import os
import io
import stat
import time
import re
import sys
import paramiko

AUTH_METHOD_PASSWORD = 0	# 0: username and password	
AUTH_METHOD_PRIVATEKEY = 1	# 1: username and private_key	
AUTH_METHOD_GSSAPI = 2		# 2: username and gssapi	

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
		auth_parameter = {}
		connect_parameter = {}
		if isinstance(user_parameter["remote_path"],str):
			user_parameter["remote_path"] = [user_parameter["remote_path"]]
		user_parameter_keys = user_parameter.keys()
		if ("username" in user_parameter_keys and
			"password" in user_parameter_keys and
			"hostname" in user_parameter_keys
			):
			auth_parameter = {
				"username":user_parameter.get("username"),
				"hostname":user_parameter.get("hostname"),
				"password":user_parameter.get("password"),
				"save_password":user_parameter.get("save_password",True)
			}
			auth_method = AUTH_METHOD_PASSWORD
		elif ("username" in user_parameter_keys and
			"hostname" in user_parameter_keys and
			"private_key" in user_parameter_keys and
			len(user_parameter.get("private_key")) == 2 and
			user_parameter.get("private_key")[0] in ["RSAKey","DSSKey","ECDSAKey","Ed25519Key"]
			):
			private_key = user_parameter.get("private_key")
			private_key[1] = os.path.expanduser(os.path.expandvars(private_key[1]))
			auth_parameter = {
				"username":user_parameter.get("username"),
				"hostname":user_parameter.get("hostname"),
				"private_key":private_key,
				"need_passphrase":user_parameter.get("need_passphrase",False)
			}
			auth_method = AUTH_METHOD_PRIVATEKEY
		elif("username" in user_parameter_keys and
			"gss_host" in user_parameter_keys and
			"gss_auth" in user_parameter_keys and
			"gss_kex" in user_parameter_keys and
			"gss_deleg_creds" in user_parameter_keys and
			"gss_trust_dns" in user_parameter_keys):
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
		connect_parameter["remote_path"] = user_parameter["remote_path"]
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
		if not isinstance(config["remote_path"],list) or isinstance(config["remote_path"],str):error_list.append("remote_path")
		if not isinstance(config["local_path"],str):error_list.append("local_path")
		if not isinstance(config["always_fingerprint_confirm"],bool):error_list.append("always_fingerprint_confirm")
		if not isinstance(config["sftp_shell"],bool):error_list.append("sftp_shell")
		if not isinstance(config["network_timeout"],int):error_list.append("network_timeout")
		if not (isinstance(config["port"],int)):error_list.append("port")
		if (not os.path.exists(os.path.expanduser(os.path.expandvars(config["known_hosts_file"]))) and config["known_hosts_file"] != ""):
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
					not os.path.exists(os.path.expanduser(os.path.expandvars(config["private_key"][1])))):
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

	def save_config(self,config=None):
		server_name = self.server_name
		save_config = config if config else self.config
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


class SSHClient():
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
		self.umask = None
		self.userid = (0,(0)) # (uid,(gid...))
		self.env = None
		self.command_ref = None
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
		user_settings_config["local_path"] = os.path.normpath(os.path.expanduser(os.path.expandvars(user_settings_config["local_path"])))
		user_settings_config["known_hosts_file"] = os.path.normpath(os.path.expanduser(os.path.expandvars(user_settings_config["known_hosts_file"]))) if user_settings_config["known_hosts_file"] else ""
		self._user_settings.init_from_parameter(
			self._user_settings.server_name,
			user_settings_config
		)

	def connect(self,callback=None):
	# 如果有输入密码的环节，需要使用callback获取程序流
		user_settings = self.user_settings
		user_settings_config = user_settings.config
		port = user_settings_config["port"]
		# self.transport
		# self.sftp_client
		# self.remote_platform
		# self.env
		# self.user_settings_config
		# self.user_settings.save_config()
		hostname = None
		if user_settings.auth_method == AUTH_METHOD_GSSAPI:
			hostname = user_settings_config["gss_host"]
			self.transport.set_gss_host(
					gss_host =  user_settings_config["gss_host"],
					trust_dns = user_settings_config["gss_trust_dns"],
					gssapi_requested = user_settings_config["gss_auth"] or user_settings_config["gss_kex"]
				)
		else:
			hostname = user_settings_config["hostname"]
		try:
			self.transport = paramiko.Transport(sock=(hostname,port))
		except Exception as e:
			LOG.E("Connect Failed",str(e.args))
		hostkeys = paramiko.HostKeys()
		need_fingerprint_confirm = user_settings_config.get("always_fingerprint_confirm",False)
		known_hosts_file = user_settings_config["known_hosts_file"]
		if known_hosts_file != "": # 如果设置known_hosts_file使用其中的认证加密方式
			hostkeys.load(known_hosts_file)
			trust_kexs = hostkeys.lookup(hostname)
			if trust_kexs:
				kexs_tuple = tuple(trust_kexs.keys())
				LOG.D("set trust_kex from known_hosts_file:",str(kexs_tuple))
				self.transport.get_security_options().key_types = kexs_tuple
			else:
				need_fingerprint_confirm = True # 当完成连接并获取到指纹后需要对指纹进行确认
		event = threading.Event() # 监听协商结束
		self.transport.start_client(event=event,timeout=user_settings_config["network_timeout"])

		start_time = time.time()
		while True: # 等待start_client返回
			event.wait(0.1)
			if event.is_set():
				if not self.transport.is_active(): # 协商失败
					time_use = time.time() - start_time
					LOG.E("Negotiation Failed",{
						"error": self.transport.get_exception().args,
						"timeout": time_use > user_settings_config["network_timeout"]
					})
				else: # 协商成功
					LOG.I("Negotiation Successful")
				break

		server_pkey = self.transport.get_remote_server_key() # 服务器公钥
		server_fingerprint = "%s:%s"%pkey_fingerprint(server_pkey)   # 服务器公钥指纹

		if need_fingerprint_confirm: # 确认添加服务器公钥指纹
			LOG.W("host no such in known_hosts,please confirm whether you trust this host",
					{
						"hostname":hostname,
						"key_name":server_pkey.get_name(),
						"fingerprint":server_fingerprint
					}
				)
			if sublime.yes_no_cancel_dialog(
			"Are you sure you want to continue connecting (yes/no)?",
			"yes",
			"no") == sublime.DIALOG_YES:
				hostkeys.add(hostname,server_pkey.get_name(),server_pkey)
				if known_hosts_file != "" and sublime.yes_no_cancel_dialog(
				"save host public key to %s ?"%known_hosts_file) == sublime.DIALOG_YES:
					hostkeys.save(known_hosts_file)
					LOG.I("save %s to %s"%(hostname,known_hosts_file))
			else:
				LOG.I("user clean")
				self.transport.close()
				return

		def auth_done(): # 认证完成
			LOG.I("Client loaded over",{
				"time use": time.time() - start_time,
				"remote OS": self.remote_platform,
				"user": user_settings_config["username"],
				"fingerprint": server_fingerprint
			})
			LOG.D("OS ENV",self.env)
			if self.get_platform() == "windows":
				# self.interattach = self.client.exec_command(r"C:\Windows\System32\cmd.exe")
				LOG.D("Shell","cmd.exe")
			else:
				# self.interattach = self.client.exec_command("/bin/sh")
				LOG.D("Shell","bash")
			# 是否检查hostkey
			if need_fingerprint_confirm:
				hostkey = hostkeys.lookup(hostname)[server_pkey.get_name()]
				if hostkey.asbytes() == server_pkey.asbytes():
					LOG.D("HostKey check OK")
				else:
					LOG.E("REMOTE HOST IDENTIFICATION HAS CHANGED!",{
						"host fingerprint": server_fingerprint,
					})
					self.transport.close()
					return
			if callback:
				callback()
			return

		# 身份认证
		if user_settings.auth_method == AUTH_METHOD_PASSWORD:
			def auth_password(password):
				try:
					self.transport.auth_password(
						username = user_settings_config["username"],
						password = password
					)
					LOG.I("Password Authentication Successful")
					if user_settings_config["save_password"]:
						# 修改属性在load_client处执行保存
						ua = user_settings.auth_parameter
						ua["password"] = password
						user_settings.auth_parameter = ua
					self.load_client(auth_done)
				except Exception as e:
					LOG.E("Password Authentication Failed",str(e.args))
			if user_settings_config["password"] == "":
				password_input(auth_password)
			else:
				auth_password(user_settings_config["password"])

		elif user_settings.auth_method == AUTH_METHOD_PRIVATEKEY:
			pkey_kex = user_settings_config["private_key"][0]
			pkey_file = user_settings_config["private_key"][1]
			def auth_private_key(pkey):
				self.transport.auth_publickey(
					username = user_settings_config["username"],
					key = pkey
				)
				LOG.I("Key Authentication Successful")
			try:
				pkey = eval("paramiko.%s"%pkey_kex)
			except Exception as e:
				LOG.E("Key type '%s' is not available"%pkey_kex,str(e.args))
			if user_settings_config["need_passphrase"]:
				password_input(lambda passphrase: auth_private_key(pkey.from_private_key_file(pkey_file,password=passphrase)))
			else:
				try:
					auth_private_key(pkey.from_private_key_file(pkey_file))
				except Exception as e:
					LOG.E("Key Authentication Failed",str(e.args))
			self.load_client(auth_done)

		elif user_settings.auth_method == AUTH_METHOD_GSSAPI:
			try:
				if user_settings_config["gss_auth"]:
					self.transport.auth_gssapi_with_mic(
							username = user_settings_config["username"],
							gss_host = user_settings_config["gss_host"],
							gss_deleg_creds = user_settings_config["gss_deleg_creds"]
						)
					LOG.I("GSS Authentication Successful (gssapi-with-mic)")
				elif user_settings_config["gss_kex"]:
					self.transport.auth_gssapi_keyex(username=user_settings_config["username"])
					LOG.I("GSS Authentication Successful (gssapi-with-mic)")
				else:
					LOG.E("GSS options error")
			except Exception as e:
				LOG.E("GSS Authentication Failed",str(e.args))
			self.load_client(auth_done)

	def load_client(self,callback=None):
		channel = self.get_new_channel()
		channel.invoke_subsystem('sftp')
		self.sftp_client =  paramiko.SFTPClient(sock=channel)
		self.remote_platform = self.get_platform()
		self.env = self.get_env()
		self.umask = int(self.user_settings_config["umask"],8)
		self.user_settings.save_config()
		self.user_settings_config["remote_path"] = [self.remote_expandvars(rp[:-1] if rp[-1] == self.remote_os_sep and rp != "/" else rp) for rp in self.user_settings_config["remote_path"]]
		self.userid = self.get_userid()
		if callback:
			callback()

	@property
	def remote_os_sep(self):
		return "\\" if self.remote_platform == "windows" else "/"

	def get_new_channel(self):
		chan = self.transport.open_session(timeout=self.user_settings_config["network_timeout"]) # 设置打开session的timeout
		# chan.settimeout(self.user_settings_config["network_timeout"]) # 交互timeout
		chan.settimeout(0.5) # 交互timeout
		return chan

	def exec_command(self,command):
		if self.user_settings_config["sftp_shell"]:
			chan = self.get_new_channel()
			chan.exec_command(command)
			try:
				stdin = chan.makefile_stdin("wb", -1)
			except:
				stdin = None
			stdout = chan.makefile("r", -1)
			stderr = chan.makefile_stderr("r", -1)
		else:
			stdin = stdout = stderr = io.BytesIO(b"Shell is unavailable for current Session")
		return (stdin,stdout,stderr)

	def get_userid(self):
		try:
			if self.user_settings_config["sftp_shell"] and self.remote_platform == "*nix":
				cmd = "id -u && id -G"
				cmd_res = self.exec_command(cmd)[1].read().decode("utf8")
				cmd_res = cmd_res.replace("\r\n","\n")
				uid,gids,_ = cmd_res.split("\n")
				gids = (gids.split(" "))
				uid = int(uid)
				gids = tuple(int(i) for i in gids)
				LOG.D("userid",{
					"uid": uid,
					"gids":gids
				})
				return (uid,gids)
			else:
				return (0,(0))
		except:
			return (0,(0))

	def get_env(self):
		try:
			if self.user_settings_config["sftp_shell"]:
				cmd = "env"
				env = {}
				if self.remote_platform == "windows":
					cmd = "set"
				cmd_res = self.exec_command(cmd)[1].read().decode("utf8")
				cmd_res = cmd_res.replace("\r\n","\n")
				for l in cmd_res.split("\n"):
					if l != "":
						name = l[:l.index("=")]
						value = l[l.index("=")+1:]
						env[name] = value
				return env
			else:
				return {}
		except:
			return {}

	def get_platform(self):
		try:
			if self.user_settings_config["sftp_shell"]:
				test_cmd = "echo ~"
				cmd_res = self.exec_command(test_cmd)[1].read().decode("utf8")
				remote_platform = None
				if cmd_res[0] == "/":
					remote_platform = "*nix"
				elif cmd_res[0] == "~":
					remote_platform = "windows"
				return remote_platform
			else:
				if self.sftp_client.normalize('.')[0] == "/":
					remote_platform = "*nix"
				else:
					remote_platform = "unknow"
				return remote_platform
		except:
			return "unknow"

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
			return remote_env.get(env_name.upper(),env_str)
		remote_path = re_rule.sub(env_replace,path)
		if remote_path[-1] == self.remote_os_sep:
			remote_path = remote_path[:-1]
		return remote_path

	def disconnect(self):
		LOG.I(self.user_settings.server_name+" close")
		self.sftp_client.close()
		self.transport.close()

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

	def file_sync(self,local_path,remote_path,dir,transfer_callback=None,sync_stat=True): # 写入并保持远程文件原始权限
		if dir == "put":
			self.sftp_client.put(local_path, remote_path,transfer_callback)
			if sync_stat:
				local_stat = os.stat(local_path)
				local_atime = local_stat.st_atime
				local_mtime = local_stat.st_mtime
				self.sftp_client.utime(remote_path,(local_atime,local_mtime))
				self.sftp_client.chmod(remote_path,stat.S_IMODE(local_stat.st_mode))
			LOG.D("remote:%s sync"%remote_path)
		elif dir == "get":
			os.makedirs(os.path.split(local_path)[0],exist_ok=True)
			self.sftp_client.get(remote_path,local_path,transfer_callback)
			if sync_stat:
				remote_stat = self.sftp_client.stat(remote_path)
				remote_atime = remote_stat.st_atime
				remote_mtime = remote_stat.st_mtime
				os.utime(local_path,(remote_atime,remote_mtime))
				os.chmod(local_path,stat.S_IMODE(remote_stat.st_mode))
			LOG.D("local:%s sync"%local_path)