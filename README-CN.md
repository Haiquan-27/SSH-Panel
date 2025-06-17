SSH-Panel
=========
此插件可用于在Sublime Text中浏览和编辑SSH服务器上的文件

支持连接任何启用openssh的服务器

| 多连接 | 状态信息 |
|--------------|---------------|
| ![Screenshot](https://raw.githubusercontent.com/Haiquan-27/SSH-Panel-doc-annex/main/w1.png)          | ![Screenshot](https://raw.githubusercontent.com/Haiquan-27/SSH-Panel-doc-annex/main/w3.png)         |

| 文件操作 | 图标适配 |
|--------------|---------------|
| ![Screenshot](https://raw.githubusercontent.com/Haiquan-27/SSH-Panel-doc-annex/main/w5.png)          | ![Screenshot](https://raw.githubusercontent.com/Haiquan-27/SSH-Panel-doc-annex/main/w6.png)         |

| 文件导航 | SSH 交互式终端 |
|--------------|---------------|
| ![Screenshot](https://raw.githubusercontent.com/Haiquan-27/SSH-Panel-doc-annex/main/w7.png)          | ![Screenshot](https://raw.githubusercontent.com/Haiquan-27/SSH-Panel-doc-annex/main/w8.png)         |

# Installation

## 1. 安装此包
* 使用 Package Control(推荐)
> 打开 `Package Control: install` 菜单并键入 **"SSH-Panel"** 即可安装

* 或手动安装
> 下载项目zip文件并解压到"{插件包路径}/SSH-Panel"

## 2. 安装依赖库 (**非常重要**)
### 如果你使用Linux,需要安装 **libffi**
```bash
# if Debian / Ubuntu
sudo apt-get install libffi-dev
# if Fedora / CentOS / RHEL
sudo yum install libffi-devel
# if Arch / Manjaro `untest`
sudo pacman -S libffi
# if Opensuse `untest`
sudo zypper install libffi-devel
```
### 安装python依赖库
* 使用`ssh_panel_install_dependencies`自动安装(推荐)
打开console执行`window.run_command('ssh_panel_install_dependencies')`命令,进行自动安装
> 可选择github(默认)或gitee的仓库源
```python
window.run_command('ssh_panel_install_dependencies',args={"source":"github"}) # download from https://gitee.com/Haiquan27/SSH-Panel-doc-annex/releases/download/public/
window.run_command('ssh_panel_install_dependencies',args={"source":"gitee"})  # download from https://gitee.com/Haiquan27/SSH-Panel-doc-annex/releases/download/public/
```
![Screenshot](https://raw.githubusercontent.com/Haiquan-27/SSH-Panel-doc-annex/main/w4.png)
![Screenshot](https://raw.githubusercontent.com/Haiquan-27/SSH-Panel-doc-annex/main/w2.png)
* 或手动安装
1. 将[此项目](https://github.com/Haiquan-27/SSH-Panel-doc-annex)下载到本地
2. 根据您的系统平台和sublime text版本选择需要的文件复制到sublime text的相应加载路径中

## 3. 重启sublime text

# Settings

设置服务器连接参数

打开命令面板菜单，选择`SSH-Panel: Edit Settings`命令，编辑并保存配置文件

## 参数注解:

* `default_connect_settings` 所有连接使用的默认参数
* `server_settings` 配置连接的首选项

### 路径:
* `remote_path` 远程主机上的路径，你可以使用远程主机上的环境变量，例如"$HOME"、"%userprofile%"，值是一个路径或路径列表
	> 每个远程根路径将会被分别映射到`local_path`的子目录下，子目录名称是由路径名生成的摘要字符串
* `local_path` 用于同步的本地目录路径，如果为空将会在当前用户家目录下自动生成，可以使用本地环境变量
	> "{auto_generate}"会被替换为由配置与时间戳生成的uuid字符串,用于生成唯一的uuid路径
	> 在第一次连接后此路径将会写入到用户配置中，用于下次连接使用

### 连接和认证:
* `network_timeout` 用于认证和连接到远程主机的超时秒数
* `port` 服务器上的SSH服务端口，默认22
* `sftp_shell` 配置会话是否支持shell
> 当连接完成时，插件会向sftp shell执行"echo ~"命令，通过命令返回结果确定目标服务器的OS，以确保设置正确的路径分隔符，环境变量的值也将通过"env"命令获取
>当SFTP会话禁止shell权限时，如果'sftp_sthell'的值为true，在连接时和获取用户id时的操作将导致产生shell命令失败的超时时间，
>将`sftp_shell`设为false以避免上述情况的发生，路径分割符的设置将通过其他方式获得，同时在"remote_path"中使用的环境变量将不再可用
* `known_hosts_file` 本地know_hosts文件路径，如果设置此项则
	> 连接时使用known_hosts_file中记录的主机密钥算法
	> 如主机未在know_hosts_file中记录，则会提示是否添加主机公钥
	> 当在连接成功后得到的主机公钥与known_host_file中记录的公钥不匹配时将会警告并强制关闭当前连接
* `username` 远程主机上的用户名
* `hostname` 远程主机IP或域名
* `always_fingerprint_confirm` 每次连接要求确认主机指纹，如果设置了`known_hosts_file`则直接通过known_hosts_file验证主机指纹

#### 如果服务器使用账户密码进行认证，应使用如下选项:
* `password` 密码明文
* `save_password` 是否在配置文件中保存密码明文，如果设为false密码将在连接操作后被删除，值为bool

#### 如果服务器使用公私密钥对进行认证，应使用如下选项:
* `private_key` 用于设置加密算法和私钥文件路径，此项只在服务器要求使用公私密钥对进行认证时有效
	> 密钥算法支持"RSAKey"、"DSSKey"、"ECDSAKey"、"Ed25519Key"
	> 此项的值是一个2元素的列表，格式为[{RSAKey/DSSKey/ECDSAKey/Ed25519Key},{私钥文件路径}]
	> !! 对于密钥文件，如果你使用的sublime版本<4000 生成密钥的命令必须包括[-m PEM]参数，或对已有的私钥文件转换格式
* `"need_passphrase"` 告知插件此密钥生成时是否使用了passphrase，值为bool

#### 如果服务器使用GSSAPI进行认证，应使用如下选项:
* `gss_host` 远程主机IP或域名，如果使用此项`hostname`将不被使用
* `gss_auth` 启用gss认证，值为bool
* `gss_kex` 使用gss kex，值为bool
* `gss_deleg_creds` gss deleg creds
* `gss_trust_dns` gss trust dns

### 杂项
* `umask` 用于`*nix`文件系统中文件掩码的设置，在`Add File`和`Add Folder`上应用
* `terminus_encoding` 用于设置终端的字符编码，例如当远程主机为windows时将此项设置为所属地区常用的语言字符编码，请根据chcp代码选择字符编码[详见此处](#terminus_encoding编码表)
* `new_window` 当新建连接时打开一个新的窗口
* `reconnect_on_start` 是否在启动sublime text时自动打开上次关闭的连接
* `style_css` 自定义css样式，类型是sublime resource，默认*Packages/SSH-Panel/style.css* [详见此处](#自定义样式)
* `file_reload` 在选中文件时重新进行文件同步，可选`auto` | `always` | `never`
	- `auto` 如果文件已经被载入到本地，后续选中该文件时不会被重新载入，否则文件将被载入一次
	- `always` 无论何时选中文件，都将进行重新载入
	- `never` 不进行载入，即使选中文件
* `icon_style` 显示在文件或目录前的图标样式，值为`emjio` | `none` | `image`之一
* `icon_theme` 如果设置了`"icon_style":"image"`,则此值用于指定图标所在主题包的路径,例如这样设置：
	- `"Packages/"`  在所有的包路径下匹配
	- `"Packages/Theme - Default/"`  在特定的主题包路径下匹配
	- `"Packages/zzz A File Icon zzz/patches/general/multi/"`  如果安装了 `A File Icon` 可以使用其下的多色图标
	- `"Packages/zzz A File Icon zzz/patches/general/single/"`  如果安装了 `A File Icon` 可以使用其下的单色图标
* `icon_quality` 如果设置了`"icon_style":"image"`，则此值用于指定被显示的图标使用的分辨率前缀，此前缀一般定义在大多数主题包中图标文件名的前段，可选`""` | `"@2x"` | `"@3x"`
* `icon_color` 如果设置了`"icon_style":"image"`，则此值用于指定一般文件和目录图标的颜色，但不会影响主题包中的图标,可选`"blue"` | `"green"` | `"white"` | `"yellow"` | `"gray"`
* `nav_bar_color_change` 更改目录面板的颜色，值为-16777215~+16777215(-0xffffff~+0xffffff)，值为字符串，此值将与当前视图背景的rgb色进行加运算得到一个新的rgb色，用于区分显示导航面板视图
	> 如果想使用原视图的背景色则可设置为 "0"
* `quiet_log` 当有消息时不会立即弹出消息面板
* `debug_mode` 是否启用Debug模式

## 例子
```js
"server_settings":{
	// 连接到Debian Linux
	// 使用口令登陆
	"Debian":{
		"username":"root",
		"hostname":"192.168.1.100",
		"password":"",
		"save_password":false,
		"remote_path":[ // 添加多个路径
			"$HOME/Project", // 可使用变量
			"/var/log"
		],
		"local_path":"~/SFTP-Local/{auto_generate}"
		// ...
	},
	// 连接到Ubuntu Linux，ssh端口为2244
	// 使用rsa密钥认证
	// 指定本地同步路径
	"Ubuntu":{
		"username":"test",
		"hostname":"Ubuntu", // NetBIOS / DNS 名称
		"port":2244,
		"private_key":["RSAKey","~/.ssh/id_rsa"],
		"need_passphrase":false，
		"remote_path":[
			"/etc/apache2"
		],
		"local_path":"~/SFTP-Local/Ubuntu" // 不使用自动生成
		// ...
	},
	// 连接到Windows Server 2016
	// 使用口令登陆
	// 记住密码
	"Windows Server 2016":{
		"username":"Administrator",
		"hostname":"192.168.1.120",
		"password":"pasSSssswd@#120120",
		"save_password":true,
		"terminus_encoding":"GB2312" // 设置终端编码
		"remote_path":"D:\\Project" // 字符串路径
		"local_path":"~/SFTP-Local/{auto_generate}"
	}
	// ...
},
```

# 开始使用
打开命令选择面板并选择`SSH-Panel: Connect Server`命令

然后选择你的服务器名称进行连接

你可以在弹出的目录面板上查看和编辑服务器信息

## 快速命令按钮:
> 点击导航视图顶部`ip@username`以显示快速命令按钮
* `[?]` :帮助
* `[I]` :显示服务器信息
* `[R]` :刷新与同步文件列表
* `[E]` :编辑设置
* `[N]` :路径导航器
* `[P]` :调出状态面板
* `[T]` :伪终端
* `[$]` :SSH 交互式终端(安装[Terminus](https://packagecontrol.io/packages/Terminus)后可用)
* `[+]` :添加路径
* `[-]` :从目录视图中删除路径
你可以点击文件或目录右侧的`[...]`或`☰`按钮查看其属性或在下方创建新的对象

# 自定义样式

你可以通过自定义*style_css*项控制显示在output_panel和navication_view中的html样式

在sublime package路径下创建文件*"Packages\User\SSH-Panel\style.css"*，并设置*"style_css":"Packages\User\SSH-Panel\style.css"*

## css 类
```css
<!-- the following class will be load -->
<!-- The available syntax rules follow https://www.sublimetext.com/docs/minihtml.html -->
.keyword{}
.keyword_error{}
.symbol{}
.title_bar{}
.res_dir{}
.res_file{}
.res_focus{}
.operation_menu{}
.warning{}
.error{}
.info{}
.debug{}
.no_accessible{}
```

## terminus_encoding编码表
| windows CHCP | Encoding Name | Language  |
|--------------|---------------|-----------|
| 437          | cp437         | English (English)  |
| 720          | cp720         | العربية (Arabic)  |
| 737          | cp737         | Ελληνικά (Greek)  |
| 775          | cp775         | Balti (Baltic)  |
| 850          | cp850         | Multilingue (Multilingual)  |
| 852          | cp852         | Středoevropské (Central European) |
| 855          | cp855         | Кирилица (Cyrillic)  |
| 857          | cp857         | Türkçe (Turkish)  |
| 860          | cp860         | Português (Portuguese)  |
| 861          | cp861         | Íslenska (Icelandic)  |
| 862          | cp862         | עִבְרִית (Hebrew)  |
| 863          | cp863         | Français Canadienne (Canadian French) |
| 864          | cp864         | العربية (Arabic)  |
| 865          | cp865         | Nordsprog (Nordic)  |
| 866          | cp866         | Русский (Russian)  |
| 869          | cp869         | Ελληνικά (Greek)  |
| 874          | cp874         | ไทย (Thai)  |
| 932          | shift_jis     | 日本語 (Japanese)  |
| 936          | gb18030/gb2312| 简体中文 (Simplified Chinese)  |
| 949          | euc_kr        | 한국어 (Korean)  |
| 950          | big5          | 繁體中文 (Traditional Chinese)  |
| 1250         | windows-1250  | Středoevropské (Central European)  |
| 1251         | windows-1251  | Кирилица (Cyrillic)  |
| 1252         | windows-1252  | Западноевропейское (Western European)  |
| 1253         | windows-1253  | Ελληνικά (Greek)  |
| 1254         | windows-1254  | Türkçe (Turkish)  |
| 1255         | windows-1255  | עִבְרִית (Hebrew)  |
| 1256         | windows-1256  | العربية (Arabic)  |
| 1257         | windows-1257  | Balti (Baltic)  |
| 1258         | windows-1258  | Tiếng Việt (Vietnamese)  |
| 65001        | utf-8         | Unicode (UTF-8)  |

# 反馈
欢迎提供建议或提供代码

如果你喜欢这个项目可以给我点个star :)
