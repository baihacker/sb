import os
import sys
import shutil
import zipfile
import json
import time
import subprocess

CurrentDirectory = os.path.dirname(os.path.realpath(__file__))
#OutputDirectory = os.path.join(CurrentDirectory, 'build')
#if not os.path.exists(OutputDirectory): os.makedirs(OutputDirectory)

def find_config_file():
  compiler_file_name = 'compilers.json'

  dirs = [CurrentDirectory]

  # USERHOME
  USERHOME = os.environ.get('USERHOME', '')
  if len(USERHOME) > 0:
    dirs.append(os.path.join(USERHOME, 'config'))

  # RootDir
  ROOTDIR = os.environ.get('ROOTDIR', '')
  if len(ROOTDIR) > 0:
    dirs.append(os.path.join(ROOTDIR, 'config'))

  # dcfpe dir
  dcfpe_dir = os.path.join(os.path.dirname(os.environ['APPDATA']), 'LocalLow\\dcfpe')
  dirs.append(dcfpe_dir)

  # app data
  dirs.append(os.environ['APPDATA'])

  # path
  dirs.extend(os.environ['PATH'].split(';'))

  for dir in dirs:
    path = os.path.join(dir, compiler_file_name)
    if os.path.exists(path):
      return path

  return ''

def load_compilers():
  compiler_file = find_config_file()

  if not os.path.exists(compiler_file):
    raise Exception, 'can not file configuration file.'

  with open(compiler_file, 'r') as tempf:
    compilers = eval(tempf.read())

  return compilers

def find_compiler_base(compilers):
  for c in compilers:
    if c['name'] == '__compiler_base':
      return c
  return {}

def find_compiler(compilers, kv):
  language = kv['language']
  name = kv.get('name', '').lower()
  type = kv.get('type', '').lower()
  arch = kv.get('arch', '').lower()
  versions = kv.get('version', '-1').split('.')
  version = -1
  if len(versions) > 0:
    version = int(versions[0])

  for c in compilers:
    if len(name) > 0 and c['name'].lower() != name:
      continue
    if len(type) > 0 and c['type'].lower() != type:
      continue
    if len(arch) > 0 and c['arch'].lower() != arch:
      continue
    if version >= 0 and int(c['version'].split('.')[0]) != version:
      continue
    for instruction in c['language_detail']:
      if language in instruction['language'].split(','):
        return dict(c), dict(instruction)

  return None, None

def expand_variable(s, variables):
  for k, v in variables.items():
    s = s.replace('$(%s)'%k, v)
  return s

def set_up_environment(compiler):
  variables = compiler['variables']
  if 'env_var_keep' in compiler:
    for k, v in compiler['env_var_keep'].items():
      realv = expand_variable(v, variables)
      if k in os.environ:
        pass
      else:
        os.environ[k] = realv
  if 'env_var_merge' in compiler:
    for k, v in compiler['env_var_merge'].items():
      realv = expand_variable(v, variables)
      if k in os.environ:
        os.environ[k] = realv + os.environ[k]
      else:
        os.environ[k] = realv
  if 'env_var_replace' in compiler:
    for k, v in compiler['env_var_merge'].items():
      realv = expand_variable(v, variables)
      os.environ[k] = realv

def create_commands(files, output, kv, is_debug):
  compilers = load_compilers()
  compiler, instruction = find_compiler(compilers, kv)
  compiler_base = find_compiler_base(compilers)

  if compiler == None:
    raise Exception, 'no suitable compiler'

  #apply environment variable to variable base
  variable_base = {}
  for (k, v) in compiler_base.get('variables', {}).items():
    variable_base[k] = expand_variable(v, os.environ)

  #apply base variables
  variables = dict(variable_base)
  for (k,v) in compiler.get('variables', {}).items():
    variables[k] = expand_variable(v, variable_base)
  compiler['variables'] = variables

  clean_files = (os.path.splitext(x)[0]+'.obj' for x in files)

  #soure files
  variables['SOURCE_FILES'] = ' '.join('"%s"'%x for x in files)
  variables['SOURCE_FILE_PATH'] = files[0]
  variables['SOURCE_FILE_PATH_NO_EXT'] = os.path.splitext(files[0])[0]
  variables['SOURCE_FILE_BASENAME'] = os.path.basename(files[0])
  variables['SOURCE_FILE_BASENAME_NO_EXT'] = os.path.splitext(os.path.basename(files[0]))[0]
  variables['SOURCE_FILE_DIRNAME'] = os.path.dirname(os.path.abspath(files[0]))

  #output file
  if len(output) == 0:
    if 'default_output_file' in instruction:
      variables['OUTPUT_FILE'] = expand_variable(instruction['default_output_file'], variables)
    else:
      variables['OUTPUT_FILE'] = 'a.exe'
  else:
    variables['OUTPUT_FILE'] = output

  #extra args
  variables['EXTRA_COMPILE_ARGS'] = ''
  if is_debug and 'debug_flags' in instruction:
    variables['EXTRA_COMPILE_ARGS'] = ' '.join(instruction['debug_flags'])
  elif not is_debug and 'release_flags' in instruction:
    variables['EXTRA_COMPILE_ARGS'] = ' '.join(instruction['release_flags'])

  if 'compile_binary' in instruction:
    compile_args = ['"' + instruction['compile_binary'] + '"']
    compile_args.extend(instruction['compile_args'])
    compile_cmd = ' '.join(expand_variable(y, variables) for y in compile_args)
  else:
    compile_cmd = None

  run_args = ['"' + instruction['running_binary'] + '"']
  run_args.extend(instruction['running_args'])
  run_cmd = ' '.join(expand_variable(y, variables) for y in run_args)

  def compile():
    if compile_cmd == None:
      return 0
    env = dict(os.environ)
    set_up_environment(compiler)
    print(compile_cmd)
    ret = subprocess.call(compile_cmd)
    for x in clean_files:
      if os.path.exists(x):
        os.remove(x)
    os.environ = env;
    return ret

  def run():
    print(run_cmd)
    ret = subprocess.call(run_cmd)
    return ret

  return compile, run

def detect_language(files):
  ext2language = {
  '.c':'c',
  '.cpp':'cpp','.cc':'cpp','.hpp':'cpp','.hxx':'cpp','.cxx':'cpp',
  '.py':'python','.pyw':'python',
  '.java':'java',
  '.hs':'haskell','.lhs':'haskell','.las':'haskell',
  '.go':'go',
  '.scala':'scala'
  }
  for f in files:
    ext = os.path.splitext(f)[1]
    if ext in ext2language:
      return ext2language[ext]
  return ''

def main(argv):
  # parse cmdline
  output = ''
  files = []
  is_debug = False
  language = ''
  name = ''
  run = False

  n = len(argv)
  i = 1
  while i < n:
    if argv[i].lower() == '-o':
      output = argv[i+1]
      i += 2
    elif argv[i].lower() == '-debug':
      is_debug = True
      i += 1
    elif argv[i].lower() == '-release':
      is_debug = False
      i += 1
    elif argv[i].lower() == '-l':
      language = argv[i+1].lower()
      i += 2
    elif argv[i].lower() == '-n':
      name = argv[i+1].lower()
      i += 2
    elif argv[i].lower() == '-r':
      run = True
      i += 1
    else:
      files.append(argv[i])
      i += 1

  if len(language) == 0:
    language = detect_language(files)
  if len(language) == 0:
    raise Exception, 'unknown language'

  compile_cmd, run_cmd = create_commands(files, output, {'language': language, 'name': name}, is_debug)

  if compile_cmd() == 0 and run == True:
    run_cmd()

if __name__ == '__main__':
  main(sys.argv)
