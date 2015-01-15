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

  dirs = [CurrentDirectory, os.environ['APPDATA']]
  dirs.extend(os.environ['PATH'].split(';'))

  for dir in dirs:
    path = os.path.join(dir, compiler_file_name)
    if os.path.exists(path):
      return path

  return ''

def load_compilers():
  compiler_file = find_config_file()

  if not os.path.exists(compiler_file):
    sys.exit(-1)

  with open(compiler_file, 'r') as tempf:
    compilers = eval(tempf.read())

  return compilers

def find_compiler(compilers, kv):
  if not 'language' in kv:
    raise 'must have language'

  language = kv['language']
  name = kv.get('name', '').lower()
  type = kv.get('type', '').lower()
  arch = kv.get('arch', '').lower()
  versions = kv.get('version', '-1').split('.')
  version = -1
  if len(versions) > 0:
    version = int(versions[0])

  for c in compilers:
    if len(name) > 0 and kv['name'].lower() != name:
      continue
    if len(type) > 0 and kv['type'].lower() != type:
      continue
    if len(arch) > 0 and kv['arch'].lower() != arch:
      continue
    if version >= 0 and int(kv['version'].split('.')[0]) != version:
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

def generate_compile_cmd(compiler, instruction, files, output, is_debug):

  variables = dict(compiler.get('variables', {}))

  clean_files = (os.path.splitext(x)[0]+'.obj' for x in files)
  #soure files
  variables['SOURCE_FILES'] = ' '.join('"%s"'%x for x in files)
  variables['SOURCE_FILE_PATH'] = files[0]
  variables['SOURCE_FILE_PATH_NO_EXT'] = os.path.splitext(files[0])[0]
  variables['SOURCE_FILE_BASENAME'] = os.path.basename(files[0])
  variables['SOURCE_FILE_BASENAME_NO_EXT'] = os.path.splitext(os.path.basename(files[0]))[0]
  variables['SOURCE_FILE_DIRNAME'] = os.path.dirname(files[0])

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

  cmd = ' '.join(expand_variable(y, variables) for y in instruction['compile_cmd'])
  run = ' '.join(expand_variable(y, variables) for y in instruction['running_cmd'])

  return cmd, run, clean_files

def main(argv):
  
  # parse cmdline
  output = ''
  files = []
  is_debug = False
  language = ''
  
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
      language = argv[i+1]
      i += 2
    else:
      files.append(argv[i])
      i += 1

  ext2language = {'.c':'c','.cpp':'cpp'}
  if len(language) == 0:
    ext = os.path.splitext(files[0])[1]
    if ext in ext2language:
      language = ext2language[ext]
    else:
      raise 'unknown language'

  # prepare compiler
  compilers = load_compilers();
  compiler,instruction = find_compiler(compilers, {'language': language})
  cmd,run,clean_files = generate_compile_cmd(compiler, instruction, files, output, is_debug)
  
  # compile
  set_up_environment(compiler)
  print(cmd)
  subprocess.call(cmd)
  for x in clean_files:
    if os.path.exists(x):
      os.remove(x)
  #print('Run:')
  #print(run)
  #subprocess.call(run)

if __name__ == '__main__':
  main(sys.argv)
