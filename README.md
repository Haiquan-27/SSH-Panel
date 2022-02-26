SSH-Panel
=========

This Sublime Text plugin allow you to browse and edit files on remote servers

Windows and Linux servers that support any openssh available

[此处](https://github.com/Haiquan-27/SSH-Panel/blob/main/README-CN.md)中文文档

![Screenshot](https://github.com/Haiquan-27/SSH-Panel-doc-annex/blob/main/recording.gif?raw=true)
# Installation

## 1. Check dependent Libraries (**very important**)
### on Windows you need:
* python3.dll
> you can install from [this repositories](https://github.com/Haiquan-27/SSH-Panel-doc-annex) and copy to **installation directory** of sublime

### on Linux you need:
* install **libffi**
```bash
# if Debian / Ubuntu
apt-get install libffi-dev
# if Fedora / CentOS / RHEL
sudo yum install libffi-devel
```

### python3.8 dependent libraries following
* bcrypt
* cffi
* cryptography
* nacl
* six
> you can install from [this repositories](https://github.com/Haiquan-27/SSH-Panel-doc-annex) and copy to **Lib\python38** path of sublime

## 2. Install Plug-in
### You can using Package Control or Manual installation
* using Package Control
> Open `Package Control: install` menu and type **"SSH-Panel"** to install

* Manual installation
> Download this package as ZIP file, extract to **"{you packages path}/SSH-Panel"**

## 3. restart sublime text


# Settings

Setup service connect parameter

open command palette and select `SSH-Panel: Edit Settings` command to edit settings file

## parameter description:

### root:
* `default_connect_settings` All connect use default parameter values
* `server_settings` Specify preferences for connections
* `debug_mode` Debug enable switch
### path:
* `remote_path` The path on the remote host. You can use the environment variable of the remote host ,like "$HOME" or "%userprofile%"
* `local_path` Local directory for synchronization,if empty will automatically generated in the user's home directory.can use the local environment variable
### connect and authentication:
* `network_timeout` The number of timeout seconds used to authenticate and connect to the remote host
* `port` SSH service port of remote host
* `known_hosts_file` know_hosts file path at local,if filled it will be used to check the known host fingerprint and If an unknown host is found, a warning will be issued to confirm the host fingerprint(use sha256)
* `username` user name on remote host
* `hostname` remote host IP address or domain name
#### if your server uses password authentication,option is:
* `password` password plaintext
* `save_password` save password plaintext in settings file,if is false the password will be deleted in the settings after connecting
#### if your server uses private and public key authentication,option is:
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

## Example
```js
"server_settings":{
		// use password and username connect
		"MyServer0":{
			"username":"",
			"hostname":"", // ip or domain name
			"password":"", // if empty will prompt intput when connect
			"save_password":false, // (optional) default is true
			// ...
		},
		// use username and [private key] connect
		"MyServer1":{
			"username":"",
			"hostname":"",
			"private_key":["RSAKey","~/.ssh/id_rsa"],			// ssh-keygen -t rsa [-m PEM]
			// "private_key":["DSSKey","~/.ssh/id_dsa"]			// ssh-keygen -t dsa [-m PEM]
			// "private_key":["ECDSAKey","~/.ssh/id_ecdsa"]		// ssh-keygen -t ecdsa [-m PEM]
			// "private_key":["Ed25519Key","~/.ssh/id_ed25519"] // ssh-keygen -t ed25519 [-m PEM]
			"need_passphrase":false								// (optional) default is false, if is true will prompt intput when connect
			// ...
		},
		// use gssapi connect
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
open command palette and select `SSH-Panel: Connect Server` command

after select you server name to connect

you can edit and view server information on the pop-up directory panel

## quick button:
* `[I]` :show server infomation
* `[R]` :refresh and sync file list
* `[E]` :edit settings
* `[?]` :help
you can click the `[...]` button on the right side of the directory or file to view attribute, delete or create a new one

# Feedback
welcome report issues and commit code.

if you like this can give me star :)
