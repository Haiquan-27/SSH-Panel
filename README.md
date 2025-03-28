SSH-Panel
=========

This Sublime Text plugin allow you to browse and edit files on remote servers

Windows and Linux servers that support any openssh available

[此处](https://github.com/Haiquan-27/SSH-Panel/blob/main/README-CN.md)中文文档

| Multiple connections | Status infomation |
|--------------|---------------|
| ![Screenshot](https://raw.githubusercontent.com/Haiquan-27/SSH-Panel-doc-annex/main/w1.png)          | ![Screenshot](https://raw.githubusercontent.com/Haiquan-27/SSH-Panel-doc-annex/main/w3.png)         |

| File Operation | Icon adaptation |
|--------------|---------------|
| ![Screenshot](https://raw.githubusercontent.com/Haiquan-27/SSH-Panel-doc-annex/main/w5.png)          | ![Screenshot](https://raw.githubusercontent.com/Haiquan-27/SSH-Panel-doc-annex/main/w6.png)         |

# Installation

## 1. Install Package
* Use Package Control(recommend)
> Open Command Panel Select `Package Control: install` and type `"SSH-Panel"` to Install

* or manual install
> download project zip file and extract to "{package path}/SSH-Panel"

## 2. Install dependency (**very important**)
### if Linux,need **libffi**
```bash
# if Debian / Ubuntu
apt-get install libffi-dev
# if Fedora / CentOS / RHEL
sudo yum install libffi-devel
# if Arch / Manjaro `untest`
sudo pacman -S libffi
# if Opensuse `untest`
sudo zypper install libffi-devel
```
### install python library
* auto install with `ssh_panel_install_dependencies`(recommend)
open console and exec `window.run_command('ssh_panel_install_dependencies')`,it will automatically install the required dependencies
> you can choose download source from github(default) or gitee
```python
window.run_command('ssh_panel_install_dependencies',args={"source":"github"}) # download from https://gitee.com/Haiquan27/SSH-Panel-doc-annex/releases/download/public/
window.run_command('ssh_panel_install_dependencies',args={"source":"gitee"})  # download from https://gitee.com/Haiquan27/SSH-Panel-doc-annex/releases/download/public/
```
![Screenshot](https://raw.githubusercontent.com/Haiquan-27/SSH-Panel-doc-annex/main/w4.png)
![Screenshot](https://raw.githubusercontent.com/Haiquan-27/SSH-Panel-doc-annex/main/w2.png)
* or manual install
1. download [this project](https://github.com/Haiquan-27/SSH-Panel-doc-annex)locally
2. Select the required file and copy it to the corresponding loading path of sublime text based on your system platform and sublime text version

## 3. restart sublime text

# Settings

Setup service connect parameter

open command palette and select `SSH-Panel: Edit Settings` command to edit settings file

## parameter description:

* `default_connect_settings` All connect use default parameter values
* `server_settings` Specify preferences for connections

### path:
* `remote_path` The path on the remote host. You can use the environment variable of the remote host ,like "$HOME" or "%userprofile%",value is path name or path list
	> Each remote root path will be mapped to the subdirectory of `local_path`. The subdirectory name is the summary string generated by the path name
* `local_path` Local directory for synchronization,if empty will automatically generated in the user's home directory.can use the local environment variable
```
string "{auto_generate}" will be replaced with the UUID string generated from configuration and timestamp to generate a unique UUID path
After the first connection, this path will be save to the user configuration and using at next connection
```

### connect and authentication:
* `network_timeout` The number of timeout seconds used to authenticate and connect to the remote host
* `port` SSH service port of remote host,default is 22
* `sftp_shell` Configure whether the session supports shell
> When the connection is complete, we will try to execute "echo ~" to the sftp shell. The return result will determine the OS platform of the target server to ensure the correct path delimiter is set, and the values of the environment variables will also be obtained through the "env" command
> When shell permissions are disabled in an SFTP session, if 'sftp_sthell' is true, it will consume a timeout of shell failures when connecting and obtain user ID
> Set 'sftp_sthell' to false to avoid this situation, and the path delimiter setting will no longer depend on the shell and the environment variables used in 'remote_path' will be unavailable
* `known_hosts_file` know_hosts file path at local,if filled it will:
	> use the host key algorithm recorded in known_hosts_file when connecting
	> if host not recorded in known_hosts_file, confirm whether to add and save the host public_key when connecting
	> warn and force close connect when public_key obtained from remote host not matches public_key recorded in known_host_file
* `username` user name on remote host
* `hostname` remote host IP address or domain name
* `always_fingerprint_confirm` confirm server fingerprint every time,if `known_hosts_file` is set wile use AA to verify the host fingerprint

#### if your server uses password authentication,option is:
* `password` password plaintext
* `save_password` save password plaintext in settings file,if is false the password will be deleted in the settings after connecting

#### if your server uses private and public_key authentication,option is:
* `private_key` used to set the encryption method and private key path when logged in to the server with the key
```
 key algorithm available "RSAKey","DSSKey","ECDSAKey","Ed25519Key"
 The value is a list of 2 elements like [{RSAKey/DSSKey/ECDSAKey/Ed25519Key},{private key path}]
 !! if you sublime version < 4000 the command to generate the key must contain the [-m PEM] parameter or use a tool to convert the existing private key file format
```
* `"need_passphrase"` tells the plug-in whether a passphrase is set when generating a key pair, value is bool

#### if your server uses gssapi authentication,option is:
* `gss_host` remote host IP address or domain name,if used, the `hostname` option is not used
* `gss_auth` enable gss authentication ,valus is bool
* `gss_kex` enable gss kex,valus is bool
* `gss_deleg_creds` gss deleg creds
* `gss_trust_dns` gss trust dns

### miscellaneous
* `umask` `*nix` file system umask for `Add File` and `Add Folder`
* `terminus_encoding` The character encoding of the terminal, for example, when the remote host is Windows, set this option to the commonly used language character encoding in the region. Please select the character encoding based on the CHCP code [see details](#terminus-encoding)
* `new_window` open new window when connect created
* `reconnect_on_start` whether to automatically open the last closed connection when starting sublime text
* `style_css` Custom CSS Style,value is sublime resource,default is *Packages/SSH-Panel/style.css* [see details](#style-coustom)
* `file_reload` Execute file synchronization,chiose from `auto` | `always` | `never`
	- `auto` if file already get in local,it not will be load afterwards,or else it will be loaded once
	- `always` whenever a file is clicked,always be reload
	- `never` never reload file,even when clicked
* `icon_style` Icon style displayed in front of a directory or file,value is choice in `emjio` | `none` | `image`
* `icon_theme` if `"icon_style":"image"`,this value represents the path of the theme package where the icon is located,Example:
	- `"Packages/"`  Match from all path
	- `"Packages/Theme - Default/"`  Match within a specific Theme path
	- `"Packages/zzz A File Icon zzz/patches/general/multi/"`  if `A File Icon` already installed,multi-color icons can be used
	- `"Packages/zzz A File Icon zzz/patches/general/single/"`  if `A File Icon` already installed,single-color icons can be used
* `icon_quality` if `"icon_style":"image"`,This value is used to specify the resolution prefix used by the displayed icon, which is generally defined before the icon file name in most theme packs,chiose from `""` | `"@2x"` | `"@3x"`
* `icon_color` if `"icon_style":"image"`,this value is used to specify the color of icons for general files and directories,but it will not affect the icons in the theme pack,chiose from `"blue"` | `"green"` | `"white"` | `"yellow"` | `"gray"`
* `nav_bar_color_change` change color of the directory panel,value range is -16777215~+16777215(-0xffffff~+0xffffff) type is string,this value will be added with the RGB color of the current view background to get a new RGB color，used to distinguish the display of navigation panel views
	> if you not want to change the background color value can be set to "0"
* `quiet_log` the pop-up message panel is not displayed immediately when a message is obtained
* `debug_mode` Debug enable switch

## Example
```js
"server_settings":{
	// Connect Debian Linux,use password
	"Debian":{
		"username":"root",
		"hostname":"192.168.1.100",
		"password":"",
		"save_password":false,
		"remote_path":[ // Add multiple paths
			"$HOME/Project", // remote system variables
			"/var/log"
		],
		"local_path":"~/SFTP-Local/{auto_generate}"
		// ...
	},
	// Connect Ubuntu Linux，ssh port is 2244
	// Use RSA key authentication
	// Specify local synchronization path
	"Ubuntu":{
		"username":"test",
		"hostname":"TestServer", // NetBIOS / DNS Name
		"port":2244,
		"private_key":["RSAKey","~/.ssh/id_rsa"],
		"need_passphrase":false,
		"remote_path":[
			"/etc/apache2"
		],
		"local_path":"~/SFTP-Local/Ubuntu" // specially designated
		// ...
	},
	// Connect Windows Server 2016
	// Use Password
	// Save Password
	"Windows Server 2016":{
		"username":"Administrator",
		"hostname":"192.168.1.120",
		"password":"pasSSssswd@#120120",
		"save_password":true,
		"terminus_encoding":"GB2312" // terminal character encoding
		"remote_path":"D:\\Project" // support string path
		"local_path":"~/SFTP-Local/{auto_generate}"
	}
	// ...
},
```

# Using
open command palette and select `SSH-Panel: Connect Server` command

after select you server name to connect

you can edit and view server information on the pop-up directory panel

## quick button:
* `[?]` :help
* `[I]` :show server infomation
* `[R]` :refresh and sync file list
* `[E]` :edit settings
* `[P]` :show status panel
* `[T]` :pseudo terminal
* `[+]` :add new root path
* `[-]` :remove root path from view
you can click the `[...]` button on the right side of the directory or file to view attribute, delete or create a new one

# Style coustom

you can set *style_css* option to control display in HTML style of output_panel and navigation_view

Create file *"Packages\User\SSH-Panel\style.css"* in sublime package path and set *"style_css":"Packages\User\SSH-Panel\style.css"*

## css class
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

## Terminus encoding
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

# Feedback
welcome report issues and commit code.

if you like this can give me star :)
