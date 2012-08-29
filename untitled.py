import sublime, sublime_plugin, os, re
from asyncprocess import AsyncProcess

RESULT_VIEW_NAME = 'amdtools_view'

class AMDtoolsCommand(sublime_plugin.WindowCommand):
  def run(self):
    return

  def get_module_name(self):
    rel = self.file_name
    print  self.file_path
    if self.file_path.startswith(self.root):
      rel = self.file_path[self.root.__len__() + 1:] # +1 to skip the first /
      print rel
    module_name = re.sub('.js$','', rel)
    return module_name

  def init_output_view(self):
    if not hasattr(self, 'output_view'):
      self.output_view = self.window.get_output_panel(RESULT_VIEW_NAME)
      self.output_view.set_name(RESULT_VIEW_NAME)
    self.clear_output_view()

  def show_output_view(self):
    if self.output_panel_showed:
      return
    self.window.run_command("show_panel", {"panel": "output."+RESULT_VIEW_NAME})
    self.output_panel_showed = True

  def clear_output_view(self):
    self.output_view.set_read_only(False)
    edit = self.output_view.begin_edit()
    self.output_view.erase(edit, sublime.Region(0, self.output_view.size()))
    self.output_view.end_edit(edit)
    self.output_view.set_read_only(True)

  def put_out(self, text, end=False):
    self.output_view.set_read_only(False)
    edit = self.output_view.begin_edit()
    self.output_view.insert(edit, self.output_view.size(), text)
    self.output_view.end_edit(edit)
    self.output_view.set_read_only(True)

  def proc_out(self, proc, data, end=False):
    data = data.decode("utf-8")
    data = '\t' + data
    data = re.sub('\n','\n\t',data)
    data = data[:len(data)-1]
    self.put_out(data, end)

  def proc_out_skip_line(self, proc, data, end=False):
    data = data.decode("utf-8")
    if (data == re.sub('.js$','', self.file_name) + '\n'):
      return
    data = '\t' + data
    data = re.sub('  ','',data)
    data = re.sub('\n','\n\t',data)
    data = data[:len(data)-1]
    self.put_out(data, end)

  def proc_terminated(self, proc):
    if proc.returncode == 0:
      msg = ''
    else:
      msg = 'Make sure madge is installed (`npm install -g madge`) and in your $PATH'
    self.put_out(msg, True)

  def init(self):
    self.file_path = self.window.active_view().file_name()
    self.file_name = os.path.basename(self.file_path)
    self.root = self.window.folders()[0]
    self.is_running = True
    self.output_panel_showed = False
    self.buffered_data = ''
    self.window.run_command("show_panel", {"panel": "output."+RESULT_VIEW_NAME})
    self.init_output_view()
    self.show_output_view()

class ListDependenciesCommand(AMDtoolsCommand):
  def run(self):
    self.init()
    self.put_out('`' + self.get_module_name() + '` depends on:\n')
    cmd = 'madge -n -f AMD "' + self.window.active_view().file_name() + '"'
    #self.put_out(cmd+'\n')
    AsyncProcess(cmd, self.proc_out, self.proc_terminated)

class ListDependentCommand(AMDtoolsCommand):
  def run(self):
    self.init()
    self.put_out('`' + self.get_module_name() + '` is a dependency of:\n')
    cmd = 'madge -n -f AMD -d "' + self.get_module_name() + '" "' + self.root+'"'
    #self.put_out(cmd+'\n')
    AsyncProcess(cmd, self.proc_out, self.proc_terminated)

class ModuleInfoCommand(AMDtoolsCommand):
  def run(self):
    self.init()
    self.put_out('`' + self.get_module_name() + '` is a dependency of:\n')
    cmd = 'madge -n -f AMD -d "' + self.get_module_name() + '" "' + self.root+'"'
    #self.put_out(cmd+'\n')
    AsyncProcess(cmd, self.next, self.proc_terminated)

  def next(self, proc, data, end=False):
    self.proc_out(proc, data, end)
    self.put_out('\n`' + self.get_module_name() + '` depends on:\n')
    cmd = 'madge -n -f AMD "' + self.window.active_view().file_name() + '"'
    #self.put_out(cmd+'\n')
    AsyncProcess(cmd, self.proc_out_skip_line, self.proc_terminated)