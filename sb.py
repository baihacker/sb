#!/usr/bin/env python
import util
import os
import sys

SCRIPT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
CURRENT_DIRECTORY = os.getcwd()
CURRENT_SBRC = os.path.join(CURRENT_DIRECTORY, '.sbrc')


def make_search_dirs():
  dirs = [SCRIPT_DIRECTORY]

  # HOMEDIR
  HOMEDIR = os.environ.get('HOMEDIR', '')
  if len(HOMEDIR) > 0:
    dirs.append(os.path.join(HOMEDIR, 'config'))

  # RootDir
  ROOTDIR = os.environ.get('ROOTDIR', '')
  if len(ROOTDIR) > 0:
    dirs.append(os.path.join(ROOTDIR, 'config'))

  # dcfpe dir
  if util.IS_WIN:
    dcfpe_dir = os.path.join(os.path.dirname(os.environ['APPDATA']),
                             'LocalLow\\dcfpe')
    dirs.append(dcfpe_dir)

  # app data
  if util.IS_WIN:
    dirs.append(os.environ['APPDATA'])

  # path
  dirs.extend(os.environ['PATH'].split(util.DELIMITER))

  return dirs


def load_global_variables():
  file_name = 'config.json'

  variables = dict(os.environ)

  for dir in make_search_dirs():
    path = os.path.join(util.trans_path(dir), file_name)
    if os.path.exists(path):
      with open(path, 'r') as tempf:
        CONFIG = eval(tempf.read())
      for k, v in CONFIG['variables'].items():
        variables[k] = expand_variable(v, os.environ)
      return variables

  return variables


def find_config_file():
  compiler_file_name = 'compilers.json'

  for dir in make_search_dirs():
    path = os.path.join(util.trans_path(dir), compiler_file_name)
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


def merge_object(src, dest):
  result = dict(dest)
  for k, v in src.items():
    if k in dest and isinstance(v, dict):
      result[k] = merge_object(v, dest[k])
    else:
      result[k] = v
  return result


def resolve_compiler(internal_name, compilers):
  for item in compilers:
    ok = 'internal_name' in item and item['internal_name'] == internal_name
    ok = ok or (not 'internal_name' in item and 'name' in item and
                item['name'] == internal_name)
    if ok:
      ret = dict(item)
      if 'base' in ret:
        ret = merge_object(ret, resolve_compiler(ret['base'], compilers))
      return ret
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
    if len(name) > 0 and (not 'name' in c or c['name'].lower() != name):
      continue
    if len(type) > 0 and (not 'type' in c or c['type'].lower() != type):
      continue
    if len(arch) > 0 and (not 'arch' in c or c['arch'].lower() != arch):
      continue
    if version >= 0 and (not 'version' in c or
                         int(c['version'].split('.')[0]) != version):
      continue

    compiler = merge_object(c, resolve_compiler(
        c['base'], compilers)) if 'base' in c else dict(c)
    if not 'language_detail' in compiler:
      continue
    if language in compiler['language_detail']:
      return compiler, dict(compiler['language_detail'][language])

  return None, None


def expand_variable(s, variables):
  for k, v in variables.items():
    s = s.replace('$(%s)' % k, v)
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
    for k, v in compiler['env_var_replace'].items():
      realv = expand_variable(v, variables)
      os.environ[k] = realv


def create_commands(config):
  compilers = load_compilers()
  compiler, instruction = find_compiler(compilers, config['compiler_spec'])
  compiler_base = find_compiler_base(compilers)

  if compiler == None:
    raise Exception, 'no suitable compiler'

  files = config['files']
  output = config['output']
  is_debug = config['is_debug']

  # compute variable base based on environment variables
  global_variables = load_global_variables()
  variable_base = dict(global_variables)
  for (k, v) in compiler_base.get('variables', {}).items():
    variable_base[k] = expand_variable(v, global_variables)

  # compute variable base based on base variables
  variables = dict(variable_base)
  for (k, v) in compiler.get('variables', {}).items():
    variables[k] = expand_variable(v, variable_base)
  compiler['variables'] = variables

  clean_files = (os.path.splitext(x)[0] + '.obj' for x in files)

  #soure files
  variables['SOURCE_FILES'] = ' '.join('"%s"' % x for x in files)
  variables['SOURCE_FILE_PATH'] = files[0]
  variables['SOURCE_FILE_PATH_NO_EXT'] = os.path.splitext(files[0])[0]
  variables['SOURCE_FILE_BASENAME'] = os.path.basename(files[0])
  variables['SOURCE_FILE_BASENAME_NO_EXT'] = os.path.splitext(
      os.path.basename(files[0]))[0]
  variables['SOURCE_FILE_DIRNAME'] = os.path.dirname(os.path.abspath(files[0]))
  variables['TEMP'] = os.getenv('TEMP')
  variables['TMP'] = os.getenv('TMP')

  #output file
  if len(output) == 0:
    if 'default_output_file' in instruction:
      variables['OUTPUT_FILE'] = expand_variable(
          instruction['default_output_file'], variables)
    else:
      variables['OUTPUT_FILE'] = 'a.exe'
  else:
    variables['OUTPUT_FILE'] = expand_variable(output, variables)

  #extra args
  extra_options = []
  if is_debug and 'debug_flags' in instruction:
    extra_options.extend(instruction['debug_flags'])
  elif not is_debug and 'release_flags' in instruction:
    extra_options.extend(instruction['release_flags'])
  extra_options.extend(config['extra_options'])
  variables['EXTRA_COMPILE_ARGS'] = ' '.join(extra_options)

  if 'compile_binary' in instruction:
    compile_args = ['"' + instruction['compile_binary'] + '"']
    compile_args.extend(instruction['compile_args'])
    compile_args[0] = util.trans_path(
        expand_variable(compile_args[0], variables))
    compile_cmd = ' '.join(expand_variable(y, variables) for y in compile_args)
  else:
    compile_cmd = None

  run_args = ['"' + instruction['running_binary'] + '"']
  run_args.extend(instruction['running_args'])
  run_cmd = ' '.join(expand_variable(y, variables) for y in run_args)

  show_compile_cmd = config['show_compile_cmd']
  show_run_cmd = config['show_run_cmd']

  def compile():
    if compile_cmd == None:
      return 0
    env = dict(os.environ)
    set_up_environment(compiler)
    if show_compile_cmd:
      print(compile_cmd)
    ret = util.execute_cmd(compile_cmd)
    for x in clean_files:
      if os.path.exists(x):
        os.remove(x)
    os.environ = env
    return ret

  def run():
    if show_run_cmd:
      print(run_cmd)
    return util.execute_cmd(run_cmd)

  return compile, run


def detect_language(files):
  ext2language = {
      '.c': 'c',
      '.cpp': 'cpp',
      '.cc': 'cpp',
      '.hpp': 'cpp',
      '.hxx': 'cpp',
      '.cxx': 'cpp',
      '.py': 'python',
      '.pyw': 'python',
      '.java': 'java',
      '.hs': 'haskell',
      '.lhs': 'haskell',
      '.las': 'haskell',
      '.go': 'go',
      '.scala': 'scala'
  }
  for f in files:
    ext = os.path.splitext(f)[1]
    if ext in ext2language:
      return ext2language[ext]
  return ''


def parse_and_run(argv, config):
  if os.path.exists(CURRENT_SBRC):
    with open(CURRENT_SBRC, 'rb') as tempf:
      default_config = eval(tempf.read().decode(encoding='utf8',
                                                errors='ignore'))
      for k, v in default_config.iteritems():
        if k not in config:
          config[k] = v

  # parse cmdline
  output = config.get('output', '')
  files = config.get('files', [])
  is_debug = config.get('files', False)
  run = config.get('run', False)
  execute = config.get('execute', False)
  show_compile_cmd = config.get('show_compile_cmd', True)
  show_run_cmd = config.get('show_run_cmd', True)
  extra_options = config.get('extra_options', [])

  compiler_spec = config.get('compiler_spec', {})
  language = compiler_spec.get('language', '')
  name = compiler_spec.get('name', '')
  type = compiler_spec.get('type', '')
  arch = compiler_spec.get('arch', '')
  version = compiler_spec.get('version', '-1')

  n = len(argv)
  i = 1
  while i < n:
    handled = False
    if argv[i].lower() == '--':
      extra_options = argv[i + 1:]
      handled = True
      break
    elif argv[i][0] == '-':
      tmp = argv[i].lstrip('-').lower()
      handled = True
      if tmp == 'o':
        output = argv[i + 1]
        i += 2
      elif tmp == 'debug':
        is_debug = True
        i += 1
      elif tmp == 'release':
        is_debug = False
        i += 1
      elif tmp == 'l':
        language = argv[i + 1].lower()
        i += 2
      elif tmp == 'n':
        name = argv[i + 1].lower()
        i += 2
      elif tmp == 'a':
        arch = argv[i + 1].lower()
        i += 2
      elif tmp == 'r':
        run = True
        i += 1
      elif tmp == 'e':
        execute = True
        i += 1
      elif tmp == 'sc':
        show_compile_cmd = True
        i += 1
      elif tmp == 'hc':
        show_compile_cmd = False
        i += 1
      elif tmp == 'sr':
        show_run_cmd = True
        i += 1
      elif tmp == 'hr':
        show_run_cmd = False
        i += 1
      else:
        handled = False
    if not handled:
      files.append(argv[i])
      i += 1

  if len(language) == 0:
    language = detect_language(files)
  if len(language) == 0:
    raise Exception, 'unknown language'

  compiler_spec['language'] = language
  compiler_spec['name'] = name
  compiler_spec['type'] = type
  compiler_spec['arch'] = arch
  compiler_spec['version'] = version

  config['output'] = output
  config['files'] = files
  config['is_debug'] = is_debug
  config['compiler_spec'] = compiler_spec
  config['run'] = run
  config['execute'] = execute
  config['show_compile_cmd'] = show_compile_cmd
  config['show_run_cmd'] = show_run_cmd
  config['extra_options'] = extra_options

  compile_cmd, run_cmd = create_commands(config)

  if execute:
    return run_cmd()

  compile_ret = compile_cmd()
  if compile_ret != 0:
    return compile_ret

  if run == True:
    return run_cmd()

  return 0


def main(argv):
  return parse_and_run(argv, {})


if __name__ == '__main__':
  sys.exit(main(sys.argv))