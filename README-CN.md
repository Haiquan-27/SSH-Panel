SSH-Panel
=========
这个Sublime Text插件可用于浏览和编辑远程服务器上的文件

支持可使用openssh的Windows、Linux服务器

![Screenshot](https://github.com/Haiquan-27/SSH-Panel-doc-annex/blob/main/recording.gif?raw=true)
# Install

## 1. 检查依赖库 (**非常重要**)
### 在Windows上你需要:
* python3.dll
> 你可以从[这个仓库](https://github.com/Haiquan-27/SSH-Panel-doc-annex)下载并复制到sublime text的**安装目录**下

### 在Linux上你需要:
* 安装 **libffi**
```bash
# if Debian / Ubuntu
apt-get install libffi-dev
# if Fedora / CentOS / RHEL
sudo yum install libffi-devel
```

### 以下python3.8依赖库
* bcrypt
* cffi
* cryptography
* nacl
* six
> 你可以从[这个仓库](https://github.com/Haiquan-27/SSH-Panel-doc-annex)下载并复制到sublime text 的**Lib\python38**路径下

## 2. 安装插件
### 你可以使用*Package Control*安装或*手动安装*
* 使用 Package Control
> 打开 `Package Control: install` 菜单并键入 **"SSH-Panel"** 即可安装

* 手动安装
> 下载项目zip文件并解压到**"{你的插件包路径}/SSH-Panel"**

## 3. 重启sublime text


# Settings

设置服务器连接参数

打开命令面板菜单，选择`SSH-Panel: Edit Settings`命令，编辑配置文件

## 参数注解:

### 根下:
* `default_connect_settings` 所有连接使用的默认参数
* `server_settings` 配置连接的首选项
* `debug_mode` 是否启用Debug模式
### 路径:
* `remote_path` 远程主机上的路径，你可以使用远程主机上的环境变量，例如"$HOME"、"%userprofile%"
* `local_path` 用于同步的本地目录路径，如果为空将会在当前用户家目录下自动生成，可以使用本地环境变量
### 连接和认证:
* `network_timeout` 用于认证和连接到远程主机的超时秒数
* `port` 服务器上的SSH服务端口
* `known_hosts_file` 本地know_hosts文件路径，如果填写将会使用其检查已知主机且如果连接了未知主机将会发出警告要求确认主机指纹(使用sha256)
* `username` 远程主机上的用户名
* `hostname` 远程主机IP或域名
#### 如果服务器使用账户密码进行认证，应使用如下选项:
* `password` 密码明文
* `save_password` 是否在配置文件中保存密码明文，如果设为false密码将在连接操作后被删除，值为bool
#### 如果服务器使用公私密钥对进行认证，应使用如下选项:
* `private_key` 用于设置加密算法和私钥文件路径，此项只在服务器要求使用公私密钥对进行认证时有效
```
 密钥算法支持"RSAKey"、"DSSKey"、"ECDSAKey"、"Ed25519Key"
 此项的值是一个2元素的列表，格式为[{RSAKey/DSSKey/ECDSAKey/Ed25519Key},{私钥文件路径}]
 !! 对于密钥文件，如果你使用的sublime版本<4000 生成密钥的命令必须包括[-m PEM]参数，或对已有的私钥文件转换格式
```
* `"need_passphrase"` 告知插件此密钥生成时是否使用了passphrase，值为bool
#### 如果服务器使用GSSAPI进行认证，应使用如下选项:
* `gss_host` 远程主机IP或域名，如果使用此项`hostname`将不被使用
* `gss_auth` 启用gss认证，值为bool
* `gss_kex` 使用gss kex，值为bool
* `gss_deleg_creds` gss deleg creds

## 例子
```js
"server_settings":{
		// 使用账户名和密码进行连接
		"MyServer0":{
			"username":"",
			"hostname":"", // ip或域名
			"password":"", // 如果为空将会在连接时提示输入
			"save_password":false, // (可选) 默认为true
			// ...
		},
		// 使用用户名和私钥进行连接
		"MyServer1":{
			"username":"",
			"hostname":"",
			"private_key":["RSAKey","~/.ssh/id_rsa"],			// ssh-keygen -t rsa [-m PEM]
			// "private_key":["DSSKey","~/.ssh/id_dsa"]			// ssh-keygen -t dsa [-m PEM]
			// "private_key":["ECDSAKey","~/.ssh/id_ecdsa"]		// ssh-keygen -t ecdsa [-m PEM]
			// "private_key":["Ed25519Key","~/.ssh/id_ed25519"] // ssh-keygen -t ed25519 [-m PEM]
			"need_passphrase":false								// (可选) 默认为false，如果为true将在连接时提示输入passphrase
			// ...
		},
		// 使用gssapi进行连接
		"MyServer2":{
			"username":"",
			"gss_host":"",
			"gss_auth":true,
			"gss_kex":true,
			"gss_deleg_creds":true
			// ...
		},
		// ...
	},
```

# Using
打开命令选择面板并选择`SSH-Panel: Connect Server`命令

然后选择你的服务器名称进行连接

你可以在弹出的目录面板上查看和编辑服务器信息

## 快速命令按钮:
* `[I]` :显示服务器信息
* `[R]` :刷新与同步文件列表
* `[E]` :编辑设置
* `[?]` :帮助

你可以点击文件或目录右侧的`[...]`按钮查看其属性或在下方创建新的对象

# Feedback
欢迎反馈或提供代码

如果你喜欢这个项目可以给我点个star :)
