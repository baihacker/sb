import sys
import os
import shutil
from subprocess import check_call

"""
  Set up basic development enviroment.
  Before script:
  1. Make sure enviornment variable DEVDIR exist and be a valid directory path.
  2. Make sure enviornment variable ROOTDIR exist and be a valid directory path.
  3. Make sure DEVPATH is a part of PATH.

  This script:
  1. Generates DEVPATH which includes a list of path added to PATH.
  2. If JAVAHOME exists, setup the corresponding JAVA class path.
  3. Generates CPLUS_INCLUDE_PATH.
  4. Copies vscode configurations from %ROOTDIR%\\home\\config\\vsc_config to %APPDAT%\\code
    and %ROOTDIR%\\projects\\.vscode
  5. Checks whether notepad++ is setup. (Also check whether npp.exe (a copy of notepad++.exe) exist.)
"""

if sys.hexversion > 0x03000000:
    import winreg
else:
    import _winreg as winreg

class Win32Environment:
    """Utility class to get/set windows environment variable"""

    def __init__(self, scope):
        assert scope in ('user', 'system')
        self.scope = scope
        if scope == 'user':
            self.root = winreg.HKEY_CURRENT_USER
            self.subkey = 'Environment'
        else:
            self.root = winreg.HKEY_LOCAL_MACHINE
            self.subkey = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'

    def getenv(self, name):
        key = winreg.OpenKey(self.root, self.subkey, 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(key, name)
        except WindowsError:
            value = ''
        return value

    def setenv(self, name, value):
        # Note: for 'system' scope, you must run this as Administrator
        key = winreg.OpenKey(self.root, self.subkey, 0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
        winreg.CloseKey(key)
        # For some strange reason, calling SendMessage from the current process
        # doesn't propagate environment changes at all.
        # TODO: handle CalledProcessError (for assert)
        #check_call('''\
#"%s" -c "import win32api, win32con; assert win32api.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment')"''' % sys.executable)

def setup_environment_variables():
  env_setter = Win32Environment(scope="user")

  DEVDIR = os.environ.get('DEVDIR', '')
  ROOTDIR = os.environ.get('ROOTDIR', '')
  JAVAHOME = os.environ.get('JAVA_HOME', '')

  if len(DEVDIR) == 0:
    print('Please set DEVDIR')
    os._exit(-1)
  if len(ROOTDIR) == 0:
    print('Please set ROOTDIR')
    os._exit(-1)

  USRDIR = os.path.join(ROOTDIR, 'usr')

  def add_if_exists(path, paths):
    if os.path.exists(path):
      paths.append(path)
    else:
      print("%s doesn't exists."%path)

  # dev_paths
  dev_paths = []
  add_if_exists(os.path.join(USRDIR, 'bin'), dev_paths)
  add_if_exists(os.path.join(USRDIR, 'dll'), dev_paths)
  add_if_exists(os.path.join(USRDIR, 'dll\\vc12_x86'), dev_paths)
  add_if_exists(os.path.join(USRDIR, 'dll\\vc12_x64'), dev_paths)
  add_if_exists(os.path.join(DEVDIR, 'MinGW-w64_7.2.0\\mingw64\\bin'), dev_paths)
  add_if_exists('C:\\python\\Python27', dev_paths)
  add_if_exists('C:\\python\\Python33', dev_paths)
  add_if_exists('C:\\Program Files (x86)\\Notepad++', dev_paths)
  add_if_exists('C:\\python\\pypy3-2.4.0-win32', dev_paths)
  if len(JAVAHOME) > 0:
    add_if_exists(os.path.join(JAVAHOME, 'bin'), dev_paths)
  env_setter.setenv('DEVPATH', ';'.join(dev_paths))

  # class_paths
  class_paths = []
  if len(JAVAHOME) > 0:
    add_if_exists('.', class_paths)
    add_if_exists(os.path.join(JAVAHOME, 'lib\\dt.jar'), class_paths)
    add_if_exists(os.path.join(JAVAHOME, 'lib\\tools.jar'), class_paths)
    env_setter.setenv('CLASSPATH', ';'.join(class_paths))

  # cpp_include_path
  cpp_include_paths = []
  add_if_exists(os.path.join(USRDIR, 'lib'), cpp_include_paths)
  add_if_exists(os.path.join(USRDIR, 'lib\\pe'), cpp_include_paths)
  add_if_exists(os.path.join(USRDIR, 'lib\\gmp-6.1.2\\include'), cpp_include_paths)
  env_setter.setenv('CPLUS_INCLUDE_PATH', ';'.join(cpp_include_paths))

  print ('Environment variables are set up!')

def setup_vscode():
  def force_copy(src, dest):
    if os.path.exists(dest):
      os.remove(dest)
    shutil.copyfile(src, dest)
  def create_dir_if_necessary(dir):
    if not os.path.exists(dir):
      os.mkdir(dir)

  vscode_paths = ['Code\\User', 'Code - Insiders\\User']
  user_files = ['settings.json', 'keybindings.json']
  for path in vscode_paths:
    target_dir = os.path.join(os.environ.get('APPDATA'), path)
    create_dir_if_necessary(target_dir)
    if not os.path.exists(target_dir):
      continue
    src_dir = os.path.join(os.environ.get('ROOTDIR', ''), 'home\\config\\vsc_config')
    if not os.path.exists(src_dir):
        continue
    for f in user_files:
      src_file = os.path.join(src_dir, f)
      target_file = os.path.join(target_dir, f)
      force_copy(src_file, target_file)

  project_config_dir = os.path.join(os.environ.get('ROOTDIR', ''), 'home\\config\\vsc_config\\.vscode')
  target_config_dir = os.path.join(os.environ.get('ROOTDIR', ''), 'projects\\.vscode')

  create_dir_if_necessary(target_config_dir)

  for f in os.listdir(project_config_dir):
    src_file = os.path.join(project_config_dir, f)
    target_file = os.path.join(target_config_dir, f)
    force_copy(src_file, target_file)

  print ('Visual studio code is set up!')

def check_npp():
  npp_dir = 'C:\\Program Files (x86)\\Notepad++'
  src_exe_path = os.path.join(npp_dir, 'notepad++.exe')
  dest_exe_path = os.path.join(npp_dir, 'npp.exe')
  if not os.path.exists(src_exe_path) or not os.path.exists(dest_exe_path):
    print ('Need to set up npp manually!')
  else:
    print ('Notepad++ is set up!')

def main(argv):
  setup_environment_variables()
  setup_vscode()
  check_npp()

if __name__ == '__main__':
  main(sys.argv)