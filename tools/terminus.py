import sublime
import sublime_plugin
import os
import sys
import threading
from .ssh_controller import SSHClient
from paramiko.channel import Channel as SSHChannel

Terminal_is_hook = False
# Hook modules
if "Terminus.terminus.terminal" in sys.modules:
	client_map = sys.modules["SSH-Panel.main"].client_map
	# Terminus by randy3k (https://packagecontrol.io/packages/Terminus)
	TerminusActivateCommand = sys.modules["Terminus.terminus.commands"].TerminusActivateCommand
	Terminal = sys.modules["Terminus.terminus.terminal"].Terminal
	RecencyManager = sys.modules["Terminus.terminus.recency"].RecencyManager
	TerminalPtyProcess = sys.modules["Terminus.terminus.ptty"].TerminalPtyProcess
	TerminalScreen = sys.modules["Terminus.terminus.ptty"].TerminalScreen
	TerminalStream = sys.modules["Terminus.terminus.ptty"].TerminalStream
	view_size = sys.modules["Terminus.terminus.view"].view_size
	Terminal_is_hook = True
else:
	Terminal = TerminusActivateCommand = object


class SSHPtyProcess(object):
	"""
		Compatible with ptyprocess.ptyprocess.PtyProcess interface classes
		only defined the methods that need to be used
	"""
	def __init__(self,client:SSHClient ,channel:SSHChannel):
		self.client = client
		self.shell_channel = channel
		self.pty_encoding = "utf-8"
		self.exitstatus = None

	@classmethod
	def spawn(cls, client:SSHClient ,dimensions=(24, 80), term="vt100"):
		transport = client.transport
		channel = transport.open_session()
		channel.get_pty(
			term = term,
			width = dimensions[1],
			height = dimensions[0]
		)
		channel.invoke_shell()
		inst = cls(client, channel)
		return inst

	def read(self, size=1024):
		if not self.isalive():
			self.terminate()
			raise EOFError() # stop thread: terminal.Terminal.reader()
		res_b = self.shell_channel.recv(size)
		res = res_b.decode(self.pty_encoding,'backslashreplace')
		# "SSH\x08H-Pa\x08an\x08nel\u2002\u2007uuu"
		# b'\r\n\x1b[?2004l\rSSH\x08H-Pa\x08an\x08nel\xe2\x80\x82\xe2\x80\x87uuu\r\n'
		return res

	def write(self, s, flush=True):
		if not self.isalive():
			self.terminate()
			raise EOFError() # stop thread: terminal.Terminal.reader()
		return self.shell_channel.send(s)

	def terminate(self, force=False):
		self.shell_channel.close()
		self.exitstatus = 0

	def isalive(self):
		return not self.shell_channel.closed

	def kill(self, sig):
		self.shell_channel.close()
		self.exitstatus = -1

	def setwinsize(self, rows, cols):
		if self.isalive():
			self.shell_channel.resize_pty(cols, rows)

class SSHTerminal(Terminal):

	def start(
			self,
			ssh_client,
			default_title=None,
			title=None,
			show_in_panel=None,
			panel_name=None,
			tag=None,
			auto_close=True,
			cancellable=False,
			timeit=False
		):

		view = self.view
		if view:
			self.detached = False
			Terminal._terminals[view.id()] = self
		else:
			Terminal._detached_terminals.append(self)
			self.detached = True

		self.show_in_panel = show_in_panel
		self.panel_name = panel_name
		self.tag = tag
		self.auto_close = auto_close
		self.cancellable = cancellable
		self.timeit = timeit
		if timeit:
			self.start_time = time.time()
		self.default_title = default_title
		self.title = title

		if view:
			self.set_offset()

		size = view_size(view or sublime.active_window().active_view(), default=(40, 80), force=self._size)
		self.process = SSHPtyProcess.spawn(client=ssh_client, dimensions=size, term="xterm-256color")
		self.screen = TerminalScreen(
			size[1], size[0], process=self.process, history=10000,
			clear_callback=self.clear_callback, reset_callback=self.reset_callback)
		self.stream = TerminalStream(self.screen)

		self.screen.set_show_image_callback(self.show_image)

		self._start_rendering()

class SshTerminusActivateCommand(TerminusActivateCommand):

	def run(self,_ , client_id):
		view = self.view
		view.run_command("terminus_initialize_view")
		client = client_map.get(client_id)
		SSHTerminal.cull_terminals()
		terminal = SSHTerminal(view)
		terminal.start(
			ssh_client=client,
			default_title="",
			title=None,
			show_in_panel=False,
			panel_name="Terminus",
			tag=None,
			auto_close=True,
			cancellable=True,
			timeit=False
		)
		recency_manager = RecencyManager.from_view(view)
		if recency_manager:
			RecencyManager.from_view(view).set_recent_terminal(view)