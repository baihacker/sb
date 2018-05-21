import sys
import os
import shutil
from subprocess import check_call

"""
  Set up basic development environment.
  Before script:
  1. Make sure environment variable DEVDIR exist and be a valid directory path.
  2. Make sure ROOTDIR\app\DevSoft be a valid directory path.
  3. Make sure DEVPATH is a part of PATH, i.e PATH=%DEVPATH%;...

  This script:
  1. Check environment variables.
  2. Create directories if necessary.
  3. Copy sb files to destination dirs.
  4. Generates DEVPATH which includes a list of path added to PATH.
  5. If JAVAHOME exists, setup the corresponding JAVA class path.
  6. Generates CPLUS_INCLUDE_PATH.
  7. Copies vscode configurations from CURRENT_DIR\\vsc_config to %APPDAT%\\code
    and %ROOTDIR%\\projects\\.vscode and %ROOTDIR%\\home\\config\\vsc_config
  8. Checks whether notepad++ is setup. (Also check whether npp.exe (a copy of notepad++.exe) exist.)
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

def force_copy(src, dest):
  if os.path.exists(dest):
    os.remove(dest)
  shutil.copyfile(src, dest)

def create_dir_if_necessary(dir):
  if not os.path.exists(dir):
    os.mkdir(dir)

DEVDIR = os.environ.get('DEVDIR', '')
ROOTDIR = os.environ.get('ROOTDIR', '')
DEVDIR = os.path.join(ROOTDIR, 'app\\DevSoft')
JAVAHOME = os.environ.get('JAVA_HOME', '')
CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
RUN_FROM_GIT_REPOSITORY = os.path.exists(os.path.join(CURRENT_DIRECTORY, '.git'))

def validate_environment_variables():
  if len(DEVDIR) == 0:
    print('Please set DEVDIR')
    os._exit(-1)
  if len(ROOTDIR) == 0:
    print('Please set ROOTDIR')
    os._exit(-1)
  if not os.path.exists(DEVDIR):
    print('%s doesn\'t exist'%DEVDIR)
    os._exit(-1)
  if not os.path.isdir(DEVDIR):
    print('%s is not a directory'%DEVDIR)
    os._exit(-1)
  if not os.path.exists(ROOTDIR):
    print('%s doesn\'t exist'%ROOTDIR)
    os._exit(-1)
  if not os.path.isdir(ROOTDIR):
    print('%s is not a directory'%ROOTDIR)
    os._exit(-1)

def create_dirs():
  create_dir_if_necessary(os.path.join(ROOTDIR, 'usr'))
  create_dir_if_necessary(os.path.join(ROOTDIR, 'usr\\bin'))
  create_dir_if_necessary(os.path.join(ROOTDIR, 'home'))
  create_dir_if_necessary(os.path.join(ROOTDIR, 'home\\config'))
  create_dir_if_necessary(os.path.join(ROOTDIR, 'home\\config\\vsc_config'))
  create_dir_if_necessary(os.path.join(ROOTDIR, 'home\\config\\vsc_config\\.vscode'))
  create_dir_if_necessary(os.path.join(ROOTDIR, 'projects'))
  create_dir_if_necessary(os.path.join(ROOTDIR, 'projects\\.vscode'))

def copy_files():
  if not os.path.exists(os.path.join(CURRENT_DIRECTORY, '.git')):
    print('Skip copying files. Not a git repository!')
    return

  bin_dir = os.path.join(ROOTDIR, 'usr\\bin')
  files = ['dcj.py', 'dcj.bat', 'jr.py', 'jr.bat', 'pe++.py', 'pe++.bat', 'pe.bat', 'sb.py', 'vc++.py', 'vc++.bat']
  for f in files:
    src_file = os.path.join(CURRENT_DIRECTORY, f)
    dest_file = os.path.join(bin_dir, f)
    force_copy(src_file, dest_file)

  config_dir = os.path.join(ROOTDIR, 'home\\config')
  src_file = os.path.join(CURRENT_DIRECTORY, 'compilers.json')
  dest_file = os.path.join(config_dir, 'compilers.json')
  force_copy(src_file, dest_file)
  
  src_file = os.path.join(CURRENT_DIRECTORY, 'setup.py')
  dest_file = os.path.join(config_dir, 'setup.py')
  force_copy(src_file, dest_file)

def setup_environment_variables():
  env_setter = Win32Environment(scope="user")

  def add_if_exists(path, paths):
    if os.path.exists(path):
      paths.append(path)
    else:
      print("%s doesn't exists."%path)

  USRDIR = os.path.join(ROOTDIR, 'usr')

  # dev_paths
  dev_paths = []
  add_if_exists(os.path.join(USRDIR, 'bin'), dev_paths)
  add_if_exists(os.path.join(USRDIR, 'dll'), dev_paths)
  add_if_exists(os.path.join(USRDIR, 'dll\\vc12_x86'), dev_paths)
  add_if_exists(os.path.join(USRDIR, 'dll\\vc12_x64'), dev_paths)
  add_if_exists(os.path.join(DEVDIR, 'MinGW-x86_64-7.3.0\\mingw64\\bin'), dev_paths)
  add_if_exists('C:\\Python27', dev_paths)
  add_if_exists('C:\\python\\Python27', dev_paths)
  add_if_exists('C:\\python\\Python33', dev_paths)
  add_if_exists('C:\\python\\Python27_64', dev_paths)
  add_if_exists('C:\\python\\Python33_64', dev_paths)
  add_if_exists('C:\\python\\pypy2', dev_paths)
  add_if_exists('C:\\python\\pypy3', dev_paths)
  add_if_exists('C:\\Program Files (x86)\\Notepad++', dev_paths)
  add_if_exists('C:\\Program Files\\Notepad++', dev_paths)
  
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
  add_if_exists(os.path.join(USRDIR, 'lib'), cpp_include_paths)
  add_if_exists(os.path.join(USRDIR, 'lib\\pe'), cpp_include_paths)
  add_if_exists(os.path.join(USRDIR, 'lib\\gmp-6.1.2\\include'), cpp_include_paths)
  env_setter.setenv('CPLUS_INCLUDE_PATH', ';'.join(cpp_include_paths))

  print ('Environment variables are set up!')

def setup_vscode():
  # copy user configurations
  src_dir = os.path.join(CURRENT_DIRECTORY, 'vsc_config')
  if not os.path.exists(src_dir):
    print('There is no vsc_config in current directory. path = %s'%src_dir)
    print ('Failed to set up visual studio code!')
    return
  appdata = os.environ.get('APPDATA')
  dest_dirs = [os.path.join(appdata, path) for path in ['Code\\User', 'Code - Insiders\\User']]
  if RUN_FROM_GIT_REPOSITORY:
    dest_dirs.append(os.path.join(ROOTDIR, 'home\\config\\vsc_config'))

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
  dest_config_dirs = [os.path.join(ROOTDIR, 'projects\\.vscode')]
  if RUN_FROM_GIT_REPOSITORY:
    dest_config_dirs.append(os.path.join(ROOTDIR, 'home\\config\\vsc_config\\.vscode'))

  for f in os.listdir(src_config_dir):
    for dest_config_dir in dest_config_dirs:
      src_file = os.path.join(src_config_dir, f)
      dest_file = os.path.join(dest_config_dir, f)
      force_copy(src_file, dest_file)

  print ('Visual studio code is set up!')

def check_npp():
  found_npp = False
  for pf_path in ['C:\\Program Files (x86)', 'C:\\Program Files']:
    npp_dir = os.path.join(pf_path, 'Notepad++')
    src_exe_path = os.path.join(npp_dir, 'notepad++.exe')
    
    if not os.path.exists(src_exe_path):
      continue
    found_npp = True;

    dest_exe_path = os.path.join(npp_dir, 'npp.exe')
    if not os.path.exists(dest_exe_path):
      print ('Need to set up npp.exe manually for %s'%src_exe_path)

  if not found_npp:
    print ('Notepad++ is not set up!')

def main(argv):
  validate_environment_variables()
  create_dirs()
  copy_files()
  setup_environment_variables()
  setup_vscode()
  check_npp()

if __name__ == '__main__':
  main(sys.argv)