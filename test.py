
# 	s = UserSettings()
# 	s.init_from_settings_file("S2")
# # 	# s.server_name = "S1"
# # 	# s.auth_parameter,\
# # 	# s.connect_parameter,\
# # 	# s.auth_method = UserSettings.format_parameter(
# # 	# 					{},
# # 	# 					{
# # 	# 						"remote_path":"~/",
# # 	# 						"network_timeout":20,
# # 	# 						"port":22,
# # 	# 						# "known_hosts_file":"~/.ssh/known_hosts",
# # 	# 						"known_hosts_file":r"C:\Users\Haiquan\.ssh\known_hosts",
# # 	# 						"username":"haiquan",
# # 	# 						"hostname":"192.168.58.100",
# # 	# 						# "private_key":["RSAKey","~/.ssh/id_rsa"],
# # 	# 						"private_key":["RSAKey",r"C:\Users\Haiquan\.ssh\id_rsa"],
# # 	# 						"need_passphrase":False
# # 	# 					}
# # 	# 				)
# 	@async_run
# 	def connect_test():
# 		print(s.config)
# 		c = ClientObj(s)
# 		print("尝试连接")
# 		c.connect()
# 		print("连接完成")
# 		# print("ENV =",self.get_env())
# 		# print("abc/1.txt remote is ",self.remote_path_mapping("abc\\1.txt"))
# 		# print(self.sftp_client.lstat(self.user_settings_config["remote_path"]))
# 		# for i in self.get_dir_list(self.user_settings_config["remote_path"]):
# 		# 	print(i)
# 		# self.sync(r"E:\Desktop\test.c","/home/haiquan/Desktop/test.c"))
# 		# print(self.sftp_client.getcwd())
# 		print(c.remote_path_mapping(r"C:\Users\Haiquan\SFTP-Local\ftp\hack.c"))
# 		# s.save_config()
# 	connect_test()