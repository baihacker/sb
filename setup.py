import sys
import os
import shutil
import ctypes
import random
import stat

from subprocess import check_call
"""
  Set up basic development environment.
  Before script:
  1. Make sure environment variable ROOTDIR and HOMEDIR are valid directory path.
  2. Make sure DEVPATH is a part of PATH, i.e PATH=%DEVPATH%;...
  3. If you want to redirect Chromium directory, please provide DEVICENAME and run it in admin mode.

  This script:
  1. Check environment variables.
  2. Create directories if necessary.
  3. Copy sb files to destination dirs.
  4. Setup pe if 'git' is available.
  5. Generates DEVPATH which includes a list of path added to PATH.
  6. If JAVAHOME exists, setup the corresponding JAVA class path.
  7. Generates CPLUS_INCLUDE_PATH and LIBRARY_PATH.
  8. Copies vscode user configurations from CURRENT_DIR\\vsc_config to %APPDATA%\\code\\User, %APPDATA%\\Code - Insiders\\User and %HOMEDIR%\\config\\vsc_config. Copy vscode directory configurations from CURRENT_DIR\\vsc_config\\.vscode to %HOMEDIR%\\config\\vsc_config\\.vscode, %ROOTDIR%\\projects\\.vscode.
  9. Checks whether notepad++ is setup. (Also check whether npp.exe (a copy of notepad++.exe) exist.)
"""

testRun = False

if testRun:
  HOMEDIR = 'D:\\test\\home'
  ROOTDIR = 'D:\\test\\root'
  DEVICENAME = 'device'
else:
  HOMEDIR = os.environ.get('HOMEDIR', '')
  ROOTDIR = os.environ.get('ROOTDIR', '')
  DEVICENAME = os.environ.get('DEVICENAME', '')
TEMP_DIR = os.environ.get('TEMP', '')

CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
RUN_FROM_GIT_REPOSITORY = os.path.exists(
    os.path.join(CURRENT_DIRECTORY, '.git'))
PRIVATE_INSTALL = False

HAS_GIT = os.system('git --help > 0') == 0

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

def remove_dir(dir):
  if os.path.exists(dir):
    for root,dirs,files in os.walk(dir):
      for d in dirs:
        os.chmod(os.path.join(root, d), stat.S_IWRITE)
      for f in files:
        os.chmod(os.path.join(root, f), stat.S_IWRITE)
    shutil.rmtree(dir, True)


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


def copy_dir_to(src, dest):
  create_dir_if_absent(dest)
  for f in os.listdir(src):
    if len(f) > 0 and f[0] == '.':
      continue
    src_file = os.path.join(src, f)
    dest_file = os.path.join(dest, f)
    if os.path.isdir(src_file):
      copy_dir_to(src_file, dest_file)
    else:
      force_copy(src_file, dest_file)


def pull_git(git, target):
  tmp_dir = os.path.join(TEMP_DIR, 'sb'+str(random.random())+'.tmp')
  try:
    os.system('git clone %s "%s"'%(git, tmp_dir))
    copy_dir_to(tmp_dir, target)
  finally:
    remove_dir(tmp_dir)


def is_admin():
  try:
      return ctypes.windll.shell32.IsUserAnAdmin()
  except:
      return False


def ready_to_create_dir_symbol_link(path):
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


def validate_environment_variables():
  if len(ROOTDIR) == 0:
    print('Please set ROOTDIR')
    os._exit(-1)

  if len(HOMEDIR) == 0:
    print('Please set HOMEDIR')
    os._exit(-1)


def create_dirs():
  print('Creating directories...')
  if not os.path.exists(ROOTDIR):
    os.makedirs(ROOTDIR)
  if not os.path.exists(HOMEDIR):
    os.makedirs(HOMEDIR)
  create_dir_if_absent(os.path.join(HOMEDIR, 'usr'))
  create_dir_if_absent(os.path.join(HOMEDIR, 'usr\\bin'))
  create_dir_if_absent(os.path.join(HOMEDIR, 'usr\\bin\\sb'))
  create_dir_if_absent(os.path.join(HOMEDIR, 'usr\\include'))
  create_dir_if_absent(os.path.join(HOMEDIR, 'usr\\include\\pe'))
  create_dir_if_absent(os.path.join(HOMEDIR, 'usr\\lib'))
  create_dir_if_absent(os.path.join(HOMEDIR, 'config'))
  create_dir_if_absent(os.path.join(HOMEDIR, 'config\\vsc_config'))
  create_dir_if_absent(
      os.path.join(HOMEDIR, 'config\\vsc_config\\.vscode'))

  create_dir_if_absent(os.path.join(ROOTDIR, 'app'))
  create_dir_if_absent(os.path.join(ROOTDIR, 'app\\DevSoft'))
  create_dir_if_absent(os.path.join(ROOTDIR, 'app\\MathsSoft'))
  create_dir_if_absent(os.path.join(ROOTDIR, 'projects'))
  create_dir_if_absent(os.path.join(ROOTDIR, 'projects\\.vscode'))
  if len(DEVICENAME) > 0:
    create_dir_if_absent(os.path.join(ROOTDIR, 'devices'))
    create_dir_if_absent(os.path.join(ROOTDIR, 'devices\\%s'%DEVICENAME))
    create_dir_if_absent(os.path.join(ROOTDIR, 'devices\\%s\\Chromium'%DEVICENAME))
  print('Directories are created.')


# If the current directory is a sb repository, set up the simple build environment.
def setup_sb():
  print('\nSetting up sb...')
  if not os.path.exists(os.path.join(CURRENT_DIRECTORY, '.git')):
    print('Skip setting up simple build environment. Not a git repository!\n')
    return

  # Copy binaries to bin directory.
  target_bin_dir = os.path.join(HOMEDIR, 'usr\\bin\\sb')
  files = [
      'dcj.py', 'dcj.bat', 'jr.py', 'jr.bat', 'pe++.py', 'pe++.bat', 'pe.bat',
      'sb.py', 'vc++.py', 'vc++.bat', 'clang++.py'
  ]
  for f in files:
    src_file = os.path.join(CURRENT_DIRECTORY, f)
    dest_file = os.path.join(target_bin_dir, f)
    force_copy(src_file, dest_file)

  # Copy compilers.json and setup.py to config directory.
  target_config_dir = os.path.join(HOMEDIR, 'config')
  files = ['compilers.json', 'setup.py']
  for f in files:
    src_file = os.path.join(CURRENT_DIRECTORY, f)
    dest_file = os.path.join(target_config_dir, f)
    force_copy(src_file, dest_file)
  
  print('sb is set up.')


def setup_pe():
  print('\nSetting up pe...')
  if not HAS_GIT:
    print('Please install git first.')
    return
  pull_git('https://github.com/baihacker/pe.git', os.path.join(HOMEDIR, 'usr\\include\\pe'))
  print('pe is set up.')


def setup_environment_variables():
  print('\nBuilding environment variables...')
  env_setter = Win32Environment(scope='user')

  def add_if_exists(path, paths):
    if os.path.exists(path):
      paths.append(path)
    else:
      print("%s doesn't exists." % path)

  USRDIR = os.path.join(HOMEDIR, 'usr')
  JAVAHOME = os.environ.get('JAVA_HOME', '')

  # dev_paths
  dev_paths = []
  add_if_exists(os.path.join(USRDIR, 'bin'), dev_paths)
  add_if_exists(os.path.join(USRDIR, 'bin\\sb'), dev_paths)
  add_if_exists(os.path.join(USRDIR, 'dll'), dev_paths)
  add_if_exists(os.path.join(USRDIR, 'dll\\vc12_x86'), dev_paths)
  add_if_exists(os.path.join(USRDIR, 'dll\\vc12_x64'), dev_paths)

  add_if_exists(
      os.path.join(ROOTDIR, 'app\\DevSoft\\MinGW-x86_64-8.1.0-posix-seh-rt_v6-rev0\\mingw64\\bin'), dev_paths)
  add_if_exists(
      os.path.join(ROOTDIR, 'app\\DevSoft\\LLVM_7.0.0\\bin'), dev_paths)
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
  print('\nSetting up vscode configurations...')
  # copy user configurations
  src_dir = os.path.join(CURRENT_DIRECTORY, 'vsc_config')
  if not os.path.exists(src_dir):
    print('There is no vsc_config in current directory: %s' % src_dir)
    print('Failed to set up visual studio code!')
    return

  # copy settings.json and keybindings.json to appdata and root dir
  appdata = os.environ.get('APPDATA')
  dest_dirs = [
      os.path.join(appdata, path)
      for path in ['Code\\User', 'Code - Insiders\\User']
  ]
  dest_dirs.append(os.path.join(HOMEDIR, 'config\\vsc_config'))

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
  dest_config_dirs = [os.path.join(HOMEDIR, 'config\\vsc_config\\.vscode')]
  dest_config_dirs.append(os.path.join(ROOTDIR, 'projects\\.vscode'))
  if PRIVATE_INSTALL:
    dest_config_dirs.append(os.path.join(ROOTDIR, 'OneDrive\\projects\\.vscode'))

  for f in os.listdir(src_config_dir):
    for dest_config_dir in dest_config_dirs:
      src_file = os.path.join(src_config_dir, f)
      dest_file = os.path.join(dest_config_dir, f)
      force_copy(src_file, dest_file)

  print('Visual studio code is set up!')


def check_npp():
  print('\nCheck notepad++ installtion...')
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
  else:
    print('Notepad++ is set up!')


def setup_symlinks():
  print('\nSetting up symlinks...')
  # Redirect chromium
  if len(DEVICENAME) > 0:
    src_dir = os.path.join(os.path.dirname(os.environ['APPDATA']), 'Local\\Chromium')
    dest_dir = os.path.join(ROOTDIR, 'devices\\%s\\Chromium'%DEVICENAME)
    if ready_to_create_dir_symbol_link(src_dir):
      os.system('mklink /D "%s" "%s"'%(src_dir, dest_dir))
    else:
      print('Cannot setup symbol link from %s to %s'%(src_dir, dest_dir))
  else:
    print('Skip setup symbol from Chromium since the device name is unknown')
  print('Symlinks are set up.')


def setup_private_symlinks():
  print('\nSetting up private symlinks...')
  # Redirect home
  # src_dir = os.path.join(ROOTDIR, 'home')
  # dest_dir = HOMEDIR
  # if ready_to_create_dir_symbol_link(src_dir):
  #  os.system('mklink /D "%s" "%s"'%(src_dir, dest_dir))
  #else:
  #  print('Cannot setup symbol link from %s to %s'%(src_dir, dest_dir))

  # Redirect pe
  # src_dir = os.path.join(HOMEDIR, 'pe')
  # dest_dir = os.path.join(HOMEDIR, 'bg\\CodeDepot\\algo_new\\pe')
  # if ready_to_create_dir_symbol_link(src_dir):
  #   os.system('mklink /D "%s" "%s"'%(src_dir, dest_dir))
  # else:
  #   print('Cannot setup symbol link from %s to %s'%(src_dir, dest_dir))

  # Redirect rose_code
  # src_dir = os.path.join(HOMEDIR, 'rose_code')
  # dest_dir = os.path.join(HOMEDIR, 'bg\\CodeDepot\\algo_new\\rose_code')
  # if ready_to_create_dir_symbol_link(src_dir):
  #   os.system('mklink /D "%s" "%s"'%(src_dir, dest_dir))
  # else:
  #   print('Cannot setup symbol link from %s to %s'%(src_dir, dest_dir))

  # Redirect projects
  src_dir = os.path.join(HOMEDIR, 'projects')
  dest_dir = os.path.join(ROOTDIR, 'OneDrive\\projects')
  if ready_to_create_dir_symbol_link(src_dir):
    os.system('mklink /D "%s" "%s"'%(src_dir, dest_dir))
  else:
    print('Cannot setup symbol link from %s to %s'%(src_dir, dest_dir))

  # Redirect dev_docs
  # src_dir = os.path.join(HOMEDIR, 'dev_docs')
  # dest_dir = os.path.join(ROOTDIR, 'dev_docs')
  # if ready_to_create_dir_symbol_link(src_dir):
  #   os.system('mklink /D "%s" "%s"'%(src_dir, dest_dir))
  # else:
  #   print('Cannot setup symbol link from %s to %s'%(src_dir, dest_dir))
  print('Private symlinks are set up.')


def main(argv):
  global PRIVATE_INSTALL
  if len(argv) > 1 and argv[1] == '-b':
    PRIVATE_INSTALL = True
  validate_environment_variables()
  create_dirs()
  setup_sb()
  setup_pe()
  setup_environment_variables()
  setup_vscode()
  check_npp()
  if is_admin():
    setup_symlinks()
    if PRIVATE_INSTALL:
      setup_private_symlinks()


if __name__ == '__main__':
  main(sys.argv)
