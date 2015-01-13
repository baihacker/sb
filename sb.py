import os
import sys
import shutil
import zipfile
import json
import time
import subprocess

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

def generate_compile_cmd(compiler, language, files, output, is_debug):
  #language match
  c = {}
  for x in compiler['language_detail']:
    if x['language'].find(language) != -1:
      c = x
      break
  if not 'language' in c:
    return '', '', []
  if len(files) == 0:
    return '', '', []

  variables = {k:v for k, v in compiler['variables'].items()}

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
    if 'default_output_file' in c:
      variables['OUTPUT_FILE'] = expand_variable(c['default_output_file'], variables)
    else:
      variables['OUTPUT_FILE'] = 'a.exe'
  else:
    variables['OUTPUT_FILE'] = output

  #extra args
  variables['EXTRA_COMPILE_ARGS'] = ''
  if is_debug and 'debug_flags' in c:
    variables['EXTRA_COMPILE_ARGS'] = ' '.join(c['debug_flags'])
  elif not is_debug and 'release_flags' in c:
    variables['EXTRA_COMPILE_ARGS'] = ' '.join(c['release_flags'])

  cmd = '"%s" '%expand_variable(c['compile_binary'], variables) +\
        ' '.join(expand_variable(y, variables) for y in c['compile_args'])
  run = '"%s" '%expand_variable(c['running_binary'], variables) +\
        ' '.join(expand_variable(y, variables) for y in c['running_args'])

  return cmd, run, clean_files

CurrentDirectory = os.path.dirname(os.path.realpath(__file__))
#OutputDirectory = os.path.join(CurrentDirectory, 'build')
#if not os.path.exists(OutputDirectory): os.makedirs(OutputDirectory)

compiler_file = os.path.join(CurrentDirectory, 'vs.json')
if not os.path.exists(compiler_file):
  compiler_file = os.path.join(os.environ['APPDATA'], 'vs.json')

if not os.path.exists(compiler_file):
  for x in os.environ['PATH'].split(';'):
    t = os.path.join(x, 'vs.json')
    if os.path.exists(t):
      compiler_file = t
      break

if not os.path.exists(compiler_file):
  sys.exit(-1)

with open(compiler_file, 'r') as tempf:
  compiler = eval(tempf.read())

if not 'variables' in compiler:
  compiler['variables'] = {}

def main(argv):
  set_up_environment(compiler)
  output = ''
  files = []
  is_debug = False
  n = len(argv)
  i = 1
  while i < n:
    if argv[i].lower() == '-o':
      output = argv[i+1]
      i += 2
    elif argv[i].lower() == 'debug':
      is_debug = True
      i += 1
    elif argv[i].lower() == 'release':
      is_debug = False
      i += 1
    else:
      files.append(argv[i])
      i += 1
  cmd,run,clean_files=generate_compile_cmd(compiler, 'cpp', files, output, is_debug)
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
