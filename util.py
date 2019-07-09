#!/usr/bin/env python
import os
import sys

if os.name == 'nt':
  IS_WIN = True
  IS_LINUX = False
  DELIMITER = ';'
  PATH_SLASH = '\\'
  TEMP_DIR = os.environ.get('TEMP', '')
else:
  IS_WIN = False
  IS_LINUX = True
  DELIMITER = ':'
  PATH_SLASH = '/'
  TEMP_DIR = '/tmp'
  LINUX_HOME = os.path.expanduser("~")

def trans_path(path):
  if IS_LINUX: 
    return path.replace('\\', PATH_SLASH)
  return path

def trans_path_list(paths):
  if IS_LINUX: 
    return [trans_path(path) for path in paths]
  return paths

if IS_WIN:
  if sys.hexversion > 0x03000000:
    import winreg
  else:
    import _winreg as winreg
  from subprocess import check_call
  import subprocess

  def execute_cmd(cmd):
    return subprocess.call(cmd)

  class EnvironmentWriter:
    """Utility class to get/set windows environment variable"""

    def __init__(self):
      scope = 'user'
      assert scope in ('user', 'system')
      self.scope = scope
      if scope == 'user':
        self.root = winreg.HKEY_CURRENT_USER
        self.subkey = 'Environment'
      else:
        self.root = winreg.HKEY_LOCAL_MACHINE
        self.subkey = (r'SYSTEM\CurrentControlSet\Control\Session '
                       r'Manager\Environment')

    def getenv(self, name):
      key = winreg.OpenKey(self.root, self.subkey, 0, winreg.KEY_READ)
      try:
        value, _ = winreg.QueryValueEx(key, name)
      except WindowsError:
        value = ''
      return value

    def setenv(self, name, value):
      # Note: for 'system' scope, you must run this as Administrator
      if isinstance(value, list):
        value = DELIMITER.join(value)
      key = winreg.OpenKey(self.root, self.subkey, 0, winreg.KEY_ALL_ACCESS)
      winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
      winreg.CloseKey(key)
      # For some strange reason, calling SendMessage from the current process
      # doesn't propagate environment changes at all.
      # TODO: handle CalledProcessError (for assert)
      #check_call('''"%s" -c "import win32api, win32con; assert win32api.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment')"''' % sys.executable)

    def done(self):
      pass
else:
  def execute_cmd(cmd):
    return os.system(cmd)

  class EnvironmentWriter:
    """Utility class to set ~/.sbrc"""

    def __init__(self):
      self.content = []

    def getenv(self, name):
      return ''

    def setenv(self, name, value):
      if isinstance(value, list):
        if len(value) > 0:
          self.content.append('export %s=${%s:+${%s}:}%s'%(name, name, name, DELIMITER.join(value)))
        else:
          self.content.append('export %s=${%s:+${%s}}'%(name, name, name))
      else:
        self.content.append('export %s=%s'%(name, value))

    def done(self):
      with open('%s/.sbrc'%LINUX_HOME, 'wb') as tempf:
        tempf.write('\n'.join(self.content))