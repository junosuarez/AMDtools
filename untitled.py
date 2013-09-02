import sublime, sublime_plugin, os, re
import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from asyncprocess import AsyncProcess

class PutOutCommand(sublime_plugin.TextCommand):
    def run(self, edit, text=""):
        self.view.set_read_only(False)
        self.view.insert(edit, self.view.size(), text)
        self.view.set_read_only(True)

RESULT_VIEW_NAME = 'amdtools_view'

class AMDtoolsCommand(sublime_plugin.WindowCommand):
  def run(self):
    return

  def get_module_name(self):
    rel = self.file_name
    if self.file_path.startswith(self.root):
      rel = self.file_path[self.root.__len__() + 1:] # +1 to skip the first /
    if os.sep == "\\":
      rel = re.sub("\\\\", "/", rel)
    module_name = re.sub('\.js$', '', rel)
    return module_name

  def init_output_view(self):
    self.output_view = self.window.create_output_panel(RESULT_VIEW_NAME)
    self.window.run_command("show_panel", {"panel": "output."+RESULT_VIEW_NAME})

  def put_out(self, text):
    self.output_view.run_command("put_out", { "text": text });

  def proc_out(self, proc, data):
    data = '\t' + data
    data = re.sub('\n','\n\t',data)
    data = data[:len(data)-1]
    self.put_out(data)

  def proc_out_skip_line(self, proc, data):
    if (data == re.sub('.js$','', self.file_name) + '\n'):
      return
    data = '\t' + data
    data = re.sub('  ','',data)
    data = re.sub('\n','\n\t',data)
    data = data[:len(data)-1]
    self.put_out(data)

  def proc_terminated(self, proc):
    if proc.returncode == 0:
      msg = ''
    else:
      msg = 'Make sure madge is installed (`npm install -g madge`) and in your $PATH'
    self.put_out(msg)

  def init(self):
    self.file_path = self.window.active_view().file_name()
    self.file_name = os.path.basename(self.file_path)
    self.root = self.window.folders()[0]
    self.init_output_view()

  def list_dependencies_exec(self):
    self.put_out('`' + self.get_module_name() + '` depends on:\n')
    cmd = 'madge -n -f AMD "' + self.window.active_view().file_name() + '"'
    AsyncProcess(cmd, self.proc_out_skip_line, self.proc_terminated)

  def list_dependent_exec(self, out_cmd):
    self.put_out('`' + self.get_module_name() + '` is a dependency of:\n')
    cmd = 'madge -n -f AMD -d "' + self.get_module_name() + '" "' + self.root+'"'
    AsyncProcess(cmd, out_cmd, self.proc_terminated)

class ListDependenciesCommand(AMDtoolsCommand):
  def run(self):
    self.init()
    self.list_dependencies_exec()

class ListDependentCommand(AMDtoolsCommand):
  def run(self):
    self.init()
    self.list_dependent_exec(self.proc_out)

class ModuleInfoCommand(AMDtoolsCommand):
  def run(self):
    self.init()
    self.list_dependent_exec(self.next)

  def next(self, proc, data):
    self.proc_out(proc, data)
    self.put_out('\n')
    self.list_dependencies_exec()
