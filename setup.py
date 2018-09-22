import sys
import os
import shutil
import ctypes

from subprocess import check_call
"""
  Set up basic development environment.
  Before script:
  1. Make sure environment variable ROOTDIR and USERHOME exist and be a valid directory path.
  2. Make sure ROOTDIR\app\DevSoft be a valid directory path.
  3. Make sure DEVPATH is a part of PATH, i.e PATH=%DEVPATH%;...
  4. If you want to redirect Chromium directory, please provide DEVICENAME and run it in admin mode.

  This script:
  1. Check environment variables.
  2. Create directories if necessary.
  3. Copy sb files to destination dirs.
  4. Generates DEVPATH which includes a list of path added to PATH.
  5. If JAVAHOME exists, setup the corresponding JAVA class path.
  6. Generates CPLUS_INCLUDE_PATH.
  7. Copies vscode configurations from CURRENT_DIR\\vsc_config to %APPDATA%\\code
    and %ROOTDIR%\\projects\\.vscode and %ROOTDIR%\\config\\vsc_config
  8. Checks whether notepad++ is setup. (Also check whether npp.exe (a copy of
  notepad++.exe) exist.)
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
    key = winreg.OpenKey(self.root, self.subkey, 0, winreg.KEY_ALL_ACCESS)
    winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
    winreg.CloseKey(key)
    # For some strange reason, calling SendMessage from the current process
    # doesn't propagate environment changes at all.
    # TODO: handle CalledProcessError (for assert)
    #check_call('''"%s" -c "import win32api, win32con; assert win32api.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment')"''' % sys.executable)


def force_copy(src, dest):
  if src.lower() == dest.lower():
    return
  if os.path.exists(dest):
    os.remove(dest)
  shutil.copyfile(src, dest)


def create_dir_if_absent(dir):
  # It doesn't try to create the parents dirs
  if not os.path.exists(dir):
    os.mkdir(dir)
  if not os.path.isdir(dir):
    print('%s is not a directory' % dir)
    os._exit(-1)

def is_admin():
  try:
      return ctypes.windll.shell32.IsUserAnAdmin()
  except:
      return False

def readyToCreateDirSymLink(path):
  if not os.path.exists(path):
    parent = os.path.dirname(path)
    # create its parent directories recursively
    if not os.path.exists(parent):
      os.makedirs(parent)
    return True
  # Skip if it is an existing file
  if not os.path.isdir(path):
    return False
  # If it is an empty dir or an existing dir
  if os.stat(path).st_size == 0:
    os.rmdir(path)
    return True
  return False

USERHOME = os.environ.get('USERHOME', '')
ROOTDIR = os.environ.get('ROOTDIR', '')
DEVICENAME = os.environ.get('DEVICENAME', '')
CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
RUN_FROM_GIT_REPOSITORY = os.path.exists(
    os.path.join(CURRENT_DIRECTORY, '.git'))


def validate_environment_variables():
  if len(ROOTDIR) == 0:
    print('Please set ROOTDIR')
    os._exit(-1)

  if not os.path.exists(ROOTDIR):
    print('%s doesn\'t exist' % ROOTDIR)
    os._exit(-1)
  if not os.path.isdir(ROOTDIR):
    print('%s is not a directory' % ROOTDIR)
    os._exit(-1)
    
  if len(USERHOME) == 0:
    print('Please set USERHOME')
    os._exit(-1)

  if not os.path.exists(USERHOME):
    print('%s doesn\'t exist' % USERHOME)
    os._exit(-1)
  if not os.path.isdir(USERHOME):
    print('%s is not a directory' % USERHOME)
    os._exit(-1)


def create_dirs():
  create_dir_if_absent(os.path.join(USERHOME, 'usr'))
  create_dir_if_absent(os.path.join(USERHOME, 'usr\\bin'))
  create_dir_if_absent(os.path.join(USERHOME, 'usr\\bin\\sb'))
  create_dir_if_absent(os.path.join(ROOTDIR, 'app'))
  create_dir_if_absent(os.path.join(ROOTDIR, 'app\\DevSoft'))
  create_dir_if_absent(os.path.join(ROOTDIR, 'app\\MathsSoft'))
  create_dir_if_absent(os.path.join(ROOTDIR, 'config'))
  create_dir_if_absent(os.path.join(ROOTDIR, 'config\\vsc_config'))
  create_dir_if_absent(
      os.path.join(ROOTDIR, 'config\\vsc_config\\.vscode'))
  create_dir_if_absent(os.path.join(ROOTDIR, 'projects'))
  create_dir_if_absent(os.path.join(ROOTDIR, 'projects\\.vscode'))
  if len(DEVICENAME) > 0:
    create_dir_if_absent(os.path.join(ROOTDIR, 'devices'))
    create_dir_if_absent(os.path.join(ROOTDIR, 'devices\\%s'%DEVICENAME))
    create_dir_if_absent(os.path.join(ROOTDIR, 'devices\\%s\\Chromium'%DEVICENAME))

# Set up the simple build environment, you can onlye setup it from sb repository.
def setup_sb():
  if not os.path.exists(os.path.join(CURRENT_DIRECTORY, '.git')):
    print('Skip setting up simple build environment. Not a git repository!')
    return

  # Copy binaries to bin directory.
  target_bin_dir = os.path.join(USERHOME, 'usr\\bin\\sb')
  files = [
      'dcj.py', 'dcj.bat', 'jr.py', 'jr.bat', 'pe++.py', 'pe++.bat', 'pe.bat',
      'sb.py', 'vc++.py', 'vc++.bat'
  ]
  for f in files:
    src_file = os.path.join(CURRENT_DIRECTORY, f)
    dest_file = os.path.join(target_bin_dir, f)
    force_copy(src_file, dest_file)

  # Copy compilers.json and setup.py to config directory.
  target_config_dir = os.path.join(ROOTDIR, 'config')
  files = ['compilers.json', 'setup.py']
  for f in files:
    src_file = os.path.join(CURRENT_DIRECTORY, f)
    dest_file = os.path.join(target_config_dir, f)
    force_copy(src_file, dest_file)


def setup_environment_variables():
  env_setter = Win32Environment(scope='user')

  def add_if_exists(path, paths):
    if os.path.exists(path):
      paths.append(path)
    else:
      print("%s doesn't exists." % path)

  USRDIR = os.path.join(USERHOME, 'usr')
  JAVAHOME = os.environ.get('JAVA_HOME', '')

  # dev_paths
  dev_paths = []
  add_if_exists(os.path.join(USRDIR, 'bin'), dev_paths)
  add_if_exists(os.path.join(USRDIR, 'bin\\sb'), dev_paths)
  add_if_exists(os.path.join(USRDIR, 'dll'), dev_paths)
  add_if_exists(os.path.join(USRDIR, 'dll\\vc12_x86'), dev_paths)
  add_if_exists(os.path.join(USRDIR, 'dll\\vc12_x64'), dev_paths)

  add_if_exists(
      os.path.join(ROOTDIR, 'app\\DevSoft\\MinGW-x86_64-8.1.0\\mingw64\\bin'), dev_paths)
  add_if_exists(os.path.join(ROOTDIR, 'app\\MathsSoft\\mma'), dev_paths)

  add_if_exists('C:\\Python27', dev_paths)
  add_if_exists('C:\\python\\Python27', dev_paths)
  add_if_exists('C:\\python\\Python33', dev_paths)
  add_if_exists('C:\\python\\Python27_64', dev_paths)
  add_if_exists('C:\\python\\Python33_64', dev_paths)
  add_if_exists('C:\\python\\pypy2', dev_paths)
  add_if_exists('C:\\python\\pypy3', dev_paths)
  add_if_exists('C:\\Program Files (x86)\\Notepad++', dev_paths)
  add_if_exists('C:\\Program Files\\Notepad++', dev_paths)
  add_if_exists('C:\\Program Files (x86)\\Pari64-2-9-5', dev_paths)

  add_if_exists('C:\\Program Files\\TortoiseSVN\\bin', dev_paths)

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
  add_if_exists(os.path.join(USRDIR, 'include'), cpp_include_paths)
  add_if_exists(os.path.join(USRDIR, 'include\\pe'), cpp_include_paths)
  add_if_exists(os.path.join(USRDIR, 'include\\flint'), cpp_include_paths)
  env_setter.setenv('CPLUS_INCLUDE_PATH', ';'.join(cpp_include_paths))
  env_setter.setenv('C_INCLUDE_PATH', ';'.join(cpp_include_paths))

  # lib path
  lib_paths = []
  add_if_exists(os.path.join(USRDIR, 'lib'), lib_paths)
  env_setter.setenv('LIBRARY_PATH', ';'.join(lib_paths))

  print('Environment variables are set up!')


def setup_vscode():
  # copy user configurations
  src_dir = os.path.join(CURRENT_DIRECTORY, 'vsc_config')
  if not os.path.exists(src_dir):
    print('There is no vsc_config in current directory. path = %s' % src_dir)
    print('Failed to set up visual studio code!')
    return

  # copy settings.json and keybindings.json to appdata and root dir
  appdata = os.environ.get('APPDATA')
  dest_dirs = [
      os.path.join(appdata, path)
      for path in ['Code\\User', 'Code - Insiders\\User']
  ]
  dest_dirs.append(os.path.join(ROOTDIR, 'config\\vsc_config'))

  for dest_dir in dest_dirs:
    if not os.path.exists(dest_dir):
      continue
    for f in ['settings.json', 'keybindings.json']:
      src_file = os.path.join(src_dir, f)
      dest_file = os.path.join(dest_dir, f)
      if os.path.exists(src_file):
        force_copy(src_file, dest_file)

  # copy project configurations
  src_config_dir = os.path.join(src_dir, '.vscode')
  dest_config_dirs = [os.path.join(ROOTDIR, 'config\\vsc_config\\.vscode')]
  dest_config_dirs.append(os.path.join(ROOTDIR, 'projects\\.vscode'))
  dest_config_dirs.append(os.path.join(ROOTDIR, 'OneDrive\\projects\\.vscode'))

  for f in os.listdir(src_config_dir):
    for dest_config_dir in dest_config_dirs:
      src_file = os.path.join(src_config_dir, f)
      dest_file = os.path.join(dest_config_dir, f)
      force_copy(src_file, dest_file)

  print('Visual studio code is set up!')


def check_npp():
  found_npp = False
  for pf_path in ['C:\\Program Files (x86)', 'C:\\Program Files']:
    npp_dir = os.path.join(pf_path, 'Notepad++')
    src_exe_path = os.path.join(npp_dir, 'notepad++.exe')

    if not os.path.exists(src_exe_path):
      continue
    found_npp = True

    dest_exe_path = os.path.join(npp_dir, 'npp.exe')
    if not os.path.exists(dest_exe_path):
      print('Need to set up npp.exe manually for %s' % src_exe_path)

  if not found_npp:
    print('Notepad++ is not set up!')

def setup_symlinks():
  # Redirect chromium
  if len(DEVICENAME) > 0:
    src_dir = os.path.join(os.path.dirname(os.environ['APPDATA']), 'Local\\Chromium')
    dest_dir = os.path.join(ROOTDIR, 'devices\\%s\\Chromium'%DEVICENAME)
    if readyToCreateDirSymLink(src_dir):
      os.system('mklink /D "%s" "%s"'%(src_dir, dest_dir))
    else:
      print('Cannot setup symbol link from %s to %s'%(src_dir, dest_dir))
  else:
    print('Skip setup symbol from Chromium since the device name is unknown')

  # Redirect cloud
  src_dir = os.path.join(ROOTDIR, 'projects\\cloud')
  dest_dir = os.path.join(ROOTDIR, 'OneDrive\\projects')
  if readyToCreateDirSymLink(src_dir):
    os.system('mklink /D "%s" "%s"'%(src_dir, dest_dir))
  else:
    print('Cannot setup symbol link from %s to %s'%(src_dir, dest_dir))

def setup_private_symlinks():
  # Redirect pe
  src_dir = os.path.join(ROOTDIR, 'pe')
  dest_dir = os.path.join(USERHOME, 'bg\\CodeDepot\\algo_new\\pe')
  if readyToCreateDirSymLink(src_dir):
    os.system('mklink /D "%s" "%s"'%(src_dir, dest_dir))
  else:
    print('Cannot setup symbol link from %s to %s'%(src_dir, dest_dir))
  
  # Redirect rose_code
  src_dir = os.path.join(ROOTDIR, 'rose_code')
  dest_dir = os.path.join(USERHOME, 'bg\\CodeDepot\\algo_new\\rose_code')
  if readyToCreateDirSymLink(src_dir):
    os.system('mklink /D "%s" "%s"'%(src_dir, dest_dir))
  else:
    print('Cannot setup symbol link from %s to %s'%(src_dir, dest_dir))

def main(argv):
  validate_environment_variables()
  create_dirs()
  setup_sb()
  setup_environment_variables()
  setup_vscode()
  check_npp()
  if is_admin():
    setup_symlinks()
    if len(argv) > 1 and argv[1] == '-b':
      setup_private_symlinks()


if __name__ == '__main__':
  main(sys.argv)
