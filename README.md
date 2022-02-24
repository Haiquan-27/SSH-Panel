# SSH-Panel

This Sublime Text plugin let you to browse and edit files on remote servers

Any server that supports openssh (including windows and Linux)

![Screenshot](https://)
# Installation

Using Package Control

Open Package Control: install menu and type "SSH-Panel" to install

or Manual installation

Download this package as ZIP file, extract to "{you packages path}/SSH-Panel"

Finally,restart sublime text

# Check whether the plug-in is imported normally(for sublime text 4 you must to do)

open console panel:

if show error:
```
ImportError: DLL load failed while importing _rust
```
the possible reason is that you missing python3.dll(or python3.so) component

you can install from [here](https://) and copy to the installation path for sublime text

# Settings

Setup service parameter

open command palette and select "SSH-Panel: Edit Settings"

## parameter description:

root:
1. "default_connect_settings" All links use default parameter values
2. "server_settings" Specify preferences for connections
3. "debug_mode" Debug enable
path:
1. "remote_path" The path on the remote host. You can use the environment variable on the remote host ,like "$HOME" or "%userprofile%"
2. "local_path" Local directory for synchronization,if empty will automatically generated in the user's home directory.can use the local environment variable
connect and authentication:
1. "network_timeout" The number of timeout seconds used to authenticate and connect to the remote host
2. "port" SSH service port of remote host
3. "known_hosts_file" know_hosts file path at local,if filled,it will be used to check the known host fingerprint. If an unknown host is found, a warning will be issued to confirm the host fingerprint
	"username" user name on remote host
	"hostname" remote host IP address or domain name
	if your server uses password authentication,option is:
		"password" password plaintext
		"save_password" save password plaintext in settings file,if is false the password will be deleted in the settings after connecting
	if your server uses private and public key authentication,option is:
		"private_key" used to set the encryption method and private key path when logged in to the server with the key
						key algorithm available "RSAKey","DSSKey","ECDSAKey","Ed25519Key"
						The value is a list of 2 elements like [{RSAKey/DSSKey/ECDSAKey/Ed25519Key},{private key path}]
		!! if you sublime version < 4000 the command to generate the key must contain the [-m PEM] parameter
		"need_passphrase" tells the plug-in whether a passphrase is set when generating a key pair, value is bool
	if your server uses gssapi authentication,option is:
		"gss_host" remote host IP address or domain name,if used, the "hostname" option is not used
		"gss_auth" enable gss authentication ,valus is bool
		"gss_kex" enable gss kex,valus is bool
		"gss_deleg_creds" gss deleg creds

## Example
```json
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

open command palette and select "SSH-Panel: Connect Server"
after select you server name to connect

you can edit and view server information on the pop-up directory panel
quick button:
	[I] :show server infomation
	[R] :refresh ans sync file list
	[E] :edit settings
	[?] :help
you can click the [...] button on the right side of the directory or file to view infomation, delete or create a new one

# Feedback

welcome report issues and commit code.
if you like this can give me star :)
