import os
import _thread
import subprocess
import functools
import time
import sublime

class AsyncProcess(object):
  def __init__(self, cmd, success, err):
    self.cmd = cmd
    self.success = success
    self.err = err
    #print("DEBUG_EXEC: " + str(self.cmd))
    self.proc = subprocess.Popen(self.cmd, shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    if self.proc.stdout:
      _thread.start_new_thread(self.read_stdout, ())

    _thread.start_new_thread(self.poll, ())

  def poll(self):
    try:
      #print("waiting")
      self.proc.wait()
    except TimeoutExpired:
      #print("timeout")
      self.proc.kill()
    #print("done")
    sublime.set_timeout(functools.partial(self.err, self.proc), 0)

  def read_stdout(self):
    data = self.proc.stdout.read(2**15)
    sublime.set_timeout(functools.partial(self.success, self.proc, data), 0)
    self.proc.stdout.close()
