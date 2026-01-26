SSH-Panel Changelog
===================

v1.5.0 Latest
-------------
Fix `/` symbols not being deleted
Fix duplicate file expansion and display twice
Fix path delete failed
Fix render list sort bug
Fix file stat lost when windows upload
Fix disconnect at PC wakes up
Fix navgation view color theme lost when sublime restart
Lazy load Terminus

v1.4.1 (2025-6-22)
------------------
Fix debug code error
Rename config `nav_bar_color_change` to `nav_bar_color_offset`

v1.4.0 (2025-6-17)
------------------
Add file navigation panel
Add interactive ssh terminal with [Terminus](https://packagecontrol.io/packages/Terminus) hacking
Add file scrolling to focus
Fix `terminus_encoding` bug
Fix UI crashes

v1.3.4 (2025-4-14)
------------------
Fix Unable to use remote `/` path
Fix Connecting prematurely before entering the password resulted in failure
Add config `sftp_shell` to support SFTP mode
Add random loading animation

v1.3.3 (2025-3-13)
------------------
Fix Input panel did not unhide input after entering password
Fix The temporarily added remote path does not support environment variables

v1.3.2 (2024-9-8)
-----------------
Fix path error in `Clone Folder`
Fix `Copy Path` function of the main path nodes
Fix `Put Folder` cannot overwrite directory

v1.3.1 (2024-8-31)
------------------
Supplementary Support for Sublime Text 3211
Fix new_window error
Fix "remote_path":["$HOME"] was accidentally deleted on reconnected
Fix local_path path bug on windows
Remove inner dependencies
Add multi platform support

v1.3.0 (2024-8-10)
------------------
* Add Menu Option
- `"Copy Path"`
- `"Open Containing Folder…"`
- `"Clone Folder"`
- `"Put Folder"`
- `"Put File"`
* Add `icon_style` emjio/image
* Add Object status
* Add file extension recognition
* Add guide page
* Add busy operation lock
* Add configuration items `umask` and `terminus_encoding`
* Fix multiple display errors

v1.2.2 (2024-4-28)
------------------
* Add `[P]` show_panel function button
* Unified theme color scheme for all panels
* Fix input line break error on the bottom panel

v1.2.1 (2022-3-9)
-----------------

* Multiple remote paths can be used (using a path list)
* New Connection Authentication Method
* Optimizing UI for directory panel
* Add pseudo terminal
* Automatically reconnect when starting Sublime Text
* Customizable panel styles `(CSS)`
* Prompt to select path when uploading files
* ADD a automatic reconnection during startup
* Add a prompt when dependencies are missing

v1.0.0 (2022-2-26)
------------------

* Pass the test on `Windows 10`, `Ubuntu 1.8`
* Pass the test on sublime text version `3211`，`4107`