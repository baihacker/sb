#!/usr/bin/env python
import sys
import os
import shutil
import ctypes
import random
import stat
import util
"""
  Set up basic development environment.
  Please see README.md for how to install sb.

  This script:
    1. Check environment variables.
    2. Create directories according to config.json.
    3. Copy sb files to destination dirs.
    4. Setup pe if 'git' is available.
    5. Create environment variables according to config.json
    6. If JAVAHOME exists, setup the corresponding JAVA class path.
    7. [Windows] Copies vscode user configurations from CURRENT_DIR\\vsc_config to %APPDATA%\\code\\User, %APPDATA%\\Code - Insiders\\User and %HOMEDIR%\\config\\vsc_config.
    8. [Windows] Copy vscode directory configurations from CURRENT_DIR\\vsc_config\\.vscode to %HOMEDIR%\\config\\vsc_config\\.vscode, %ROOTDIR%\\projects\\.vscode.
    9. [Windows] Checks whether notepad3 is setup. (Also check whether np3.exe (a copy ofnotepad3.exe) exist.)
    10. Copy _vimrc to vim's dir or copy .vimrc to ~/ for linux.
"""

testRun = False

if testRun:
  HOMEDIR = 'D:\\test\\home'
  ROOTDIR = 'D:\\test\\root'
else:
  HOMEDIR = os.environ.get('HOMEDIR', '')
  ROOTDIR = os.environ.get('ROOTDIR', '')

SCRIPT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
RUN_FROM_GIT_REPOSITORY = os.path.exists(os.path.join(SCRIPT_DIRECTORY, '.git'))
CONFIG_JSON_PATH = os.path.join(SCRIPT_DIRECTORY, 'config.json')

flag_private_install = False
flag_update_vim = False
flag_setup_pe = False

config = {}

if util.IS_WIN:
  HAS_GIT = os.system('git --help 1>NUL 2>NUL') == 0
else:
  HAS_GIT = os.system('git --help > /dev/null 2>&1') == 0


def remove_dir(dir):
  if os.path.exists(dir):
    for root, dirs, files in os.walk(dir):
      for d in dirs:
        os.chmod(os.path.join(root, d), stat.S_IWRITE)
      for f in files:
        os.chmod(os.path.join(root, f), stat.S_IWRITE)
    shutil.rmtree(dir, True)


def force_copy(src, dest):
  if src.lower() == dest.lower():
    return
  src = util.trans_path(src)
  dest = util.trans_path(dest)
  if os.path.exists(dest):
    os.remove(dest)
  shutil.copyfile(src, dest)


def create_dir_if_absent(dir):
  # It doesn't try to create the parents dirs
  dir = util.trans_path(dir)
  if not os.path.exists(dir):
    os.mkdir(dir)
  if not os.path.isdir(dir):
    print('%s is not a directory' % dir)
    os._exit(-1)


def copy_dir_to(src, dest):
  src = util.trans_path(src)
  dest = util.trans_path(dest)
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
  tmp_dir = os.path.join(util.TEMP_DIR, 'sb' + str(random.random()) + '.tmp')
  try:
    os.system('git clone %s "%s"' % (git, tmp_dir))
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


def expand_variable(s, variables):
  for k, v in variables.items():
    s = s.replace('$(%s)' % k, v)
  return s


def prepare_variables():
  if len(ROOTDIR) == 0:
    print('Please set ROOTDIR')
    os._exit(-1)

  if len(HOMEDIR) == 0:
    print('Please set HOMEDIR')
    os._exit(-1)

  if not os.path.exists(CONFIG_JSON_PATH):
    print('can not file config.json.')
    os._exit(-1)

  global config

  with open(CONFIG_JSON_PATH, 'r') as tempf:
    config = eval(tempf.read())

  if not 'variables' in config:
    config['variables'] = {}

  variables = dict(os.environ)
  for k, v in config['variables'].items():
    variables[k] = expand_variable(v, os.environ)

  config['variables'] = variables

  if not 'CREATE_DIR' in config:
    config['CREATE_DIR'] = []


def create_dirs():
  print('Creating directories...')
  if not os.path.exists(ROOTDIR):
    os.makedirs(ROOTDIR)
  if not os.path.exists(HOMEDIR):
    os.makedirs(HOMEDIR)

  for item in config['CREATE_DIR']:
    target = expand_variable(item, config['variables'])
    create_dir_if_absent(target)

  print('Directories are created.')


# If the current directory is a sb repository, set up the simple build environment.
def setup_sb():
  print('\nSetting up sb...')
  if not os.path.exists(os.path.join(SCRIPT_DIRECTORY, '.git')):
    print('Skip setting up simple build environment. Not a git repository!\n')
    return

  # Copy binaries to bin directory.
  target_bin_dir = os.path.join(HOMEDIR, 'usr\\bin\\sb')
  files = [
      'clang++.py',
      'dcj.bat',
      'dcj.py',
      "e.bat",
      "e.py",
      'jr.bat',
      'jr.py',
      'pe.bat',
      'pe++',
      'pe++.bat',
      'pe++.py',
      'sb.py',
      'util.py',
      'vc++.bat',
      'vc++.py',
  ]
  for f in files:
    src_file = os.path.join(SCRIPT_DIRECTORY, f)
    dest_file = os.path.join(target_bin_dir, f)
    force_copy(src_file, dest_file)
    if util.IS_LINUX:
      os.chmod(util.trans_path(dest_file), 0777)

  # Copy compilers.json, setup.py, config.json, _vimrc to sb config directory.
  target_config_dir = os.path.join(HOMEDIR, 'config\\sb')
  files = ['compilers.json', 'setup.py', 'config.json', '_vimrc']
  for f in files:
    src_file = os.path.join(SCRIPT_DIRECTORY, f)
    dest_file = os.path.join(target_config_dir, f)
    force_copy(src_file, dest_file)

  print('sb is set up.')


def setup_pe():
  print('\nSetting up pe...')
  if not HAS_GIT:
    print('Please install git first.')
    return
  PE_DIR = util.trans_path(os.path.join(HOMEDIR, 'usr\\include\\pe'))
  pull_git('https://github.com/baihacker/pe.git', PE_DIR)
  util.execute_cmd('python "%s"' % os.path.join(PE_DIR, 'gen_config.py'))
  print('pe is set up.')


def setup_environment_variables():
  print('\nBuilding environment variables...')
  env_setter = util.EnvironmentWriter()

  def add_if_exists(path, paths):
    path = util.trans_path(path)
    if os.path.exists(path):
      paths.append(path)
    else:
      print("%s doesn't exists." % path)

  variables = config['variables']

  # Environment variables.
  path_vars = set(config['PATH_VARS'])
  for k, v in config['ENV'].items():
    values = []
    is_path = k in path_vars
    raw_values = list(v)
    if k in config['ENV_WIN']:
      raw_values.extend(config['ENV_WIN'][k])
    for value in raw_values:
      realvalue = expand_variable(value, variables)
      if is_path:
        add_if_exists(realvalue, values)
      else:
        values.append(realvalue)
    env_setter.setenv(k, values)

  # Update java class path
  JAVAHOME = os.environ.get('JAVA_HOME', '')
  class_paths = []
  if len(JAVAHOME) > 0:
    add_if_exists('.', class_paths)
    add_if_exists(os.path.join(JAVAHOME, 'lib\\dt.jar'), class_paths)
    add_if_exists(os.path.join(JAVAHOME, 'lib\\tools.jar'), class_paths)
    env_setter.setenv('CLASSPATH', class_paths)

  env_setter.done()

  print('Environment variables are set up!')


def setup_vim():
  print('\nSetting up vim...')
  if util.IS_WIN:
    vim_prefix = ['C:\\Program Files (x86)\\Vim', 'C:\\Program Files\\Vim']
    FILE_NAME = '_vimrc'
  else:
    vim_prefix = [util.LINUX_HOME]
    FILE_NAME = '.vimrc'

  src = os.path.join(SCRIPT_DIRECTORY, FILE_NAME)
  done = 0
  for dir in vim_prefix:
    target_path = os.path.join(dir, FILE_NAME)
    if os.path.exists(target_path):
      shutil.copyfile(util.trans_path(src), util.trans_path(target_path))
      print('%s is updated.' % target_path)
      done = done + 1
  if done > 0:
    print('Vim is set up.')
  else:
    print('Vim is not found.')


def setup_vscode():
  print('\nSetting up vscode configurations...')

  # copy user configurations
  src_dir = os.path.join(SCRIPT_DIRECTORY, 'vsc_config')
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
    for f in [  # 'settings.json', don't copy settings.json
        'keybindings.json'
    ]:
      src_file = os.path.join(src_dir, f)
      dest_file = os.path.join(dest_dir, f)
      if os.path.exists(src_file):
        force_copy(src_file, dest_file)

  # copy project configurations
  src_config_dir = os.path.join(src_dir, '.vscode')
  dest_config_dirs = [os.path.join(HOMEDIR, 'config\\vsc_config\\.vscode')]
  dest_config_dirs.append(os.path.join(ROOTDIR, 'projects\\.vscode'))
  if flag_private_install:
    dest_config_dirs.append(os.path.join(ROOTDIR,
                                         'OneDrive\\projects\\.vscode'))

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


def check_np3():
  print('\nCheck notepad3 installtion...')
  found_np3 = False
  for pf_path in ['C:\\Program Files (x86)', 'C:\\Program Files']:
    np3_dir = os.path.join(pf_path, 'Notepad3')
    src_exe_path = os.path.join(np3_dir, 'Notepad3.exe')

    if not os.path.exists(src_exe_path):
      continue
    found_np3 = True

    dest_exe_path = os.path.join(np3_dir, 'np3.exe')
    if not os.path.exists(dest_exe_path):
      print('Need to set up np3.exe manually for %s' % src_exe_path)

  if not found_np3:
    print('Notepad3 is not set up!')
  else:
    print('Notepad3 is set up!')


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
  # src_dir = os.path.join(HOMEDIR, 'projects')
  # dest_dir = os.path.join(ROOTDIR, 'OneDrive\\projects')
  # if ready_to_create_dir_symbol_link(src_dir):
  #  os.system('mklink /D "%s" "%s"' % (src_dir, dest_dir))
  # else:
  #  print('Cannot setup symbol link from %s to %s' % (src_dir, dest_dir))

  # Redirect dev_docs
  # src_dir = os.path.join(HOMEDIR, 'dev_docs')
  # dest_dir = os.path.join(ROOTDIR, 'dev_docs')
  # if ready_to_create_dir_symbol_link(src_dir):
  #   os.system('mklink /D "%s" "%s"'%(src_dir, dest_dir))
  # else:
  #   print('Cannot setup symbol link from %s to %s'%(src_dir, dest_dir))
  # print('Private symlinks are set up.')
  pass


def setup_symlinks():
  # print('\nSetting up symlinks...')
  # Redirect chromium
  # if len(DEVICENAME) > 0:
  # src_dir = os.path.join(os.path.dirname(os.environ['APPDATA']), 'Local\\Chromium')
  #  dest_dir = os.path.join(ROOTDIR, 'devices\\%s\\Chromium'%DEVICENAME)
  #  if ready_to_create_dir_symbol_link(src_dir):
  #    os.system('mklink /D "%s" "%s"'%(src_dir, dest_dir))
  #  else:
  #    print('Cannot setup symbol link from %s to %s'%(src_dir, dest_dir))
  # else:
  #  print('Skip setup symbol from Chromium since the device name is unknown')
  # print('Symlinks are set up.')
  if flag_private_install:
    setup_private_symlinks()


def main(argv):
  global flag_private_install
  global flag_update_vim
  global flag_setup_pe
  n = len(argv)
  i = 1
  while i < n:
    tmp = argv[i].lstrip('-').lower()
    if tmp == 'b':
      flag_private_install = True
    elif tmp == 'v':
      flag_update_vim = True
    elif tmp == 'pe':
      flag_setup_pe = True
    i += 1

  prepare_variables()
  create_dirs()
  setup_sb()

  if flag_setup_pe:
    setup_pe()
  else:
    print '\nSkip setting up pe'

  setup_environment_variables()

  if flag_update_vim:
    setup_vim()
  else:
    print '\nSkip updating vim'

  if util.IS_WIN:
    setup_vscode()
    check_np3()

    if is_admin():
      setup_symlinks()


if __name__ == '__main__':
  main(sys.argv)
