#!/usr/bin/env python
import util
import os
import sys

CURRENT_DIRECTORY = os.getcwd()
CURRENT_SBRC = os.path.join(CURRENT_DIRECTORY, '.sbrc')


def expand_variable(s, variables):
  for k, v in variables.items():
    s = s.replace('$(%s)' % k, v)
  return s


def parse_and_run(argv, config):
  if os.path.exists(CURRENT_SBRC):
    with open(CURRENT_SBRC, 'rb') as tempf:
      default_config = eval(tempf.read().decode(encoding='utf8',
                                                errors='ignore'))
      for k, v in default_config.iteritems():
        if k not in config:
          config[k] = v

  variables = {}
  variables['TEMP'] = os.getenv('TEMP')
  variables['TMP'] = os.getenv('TMP')

  output_dir = expand_variable(config.get('output_dir', ''), variables)

  files = argv[1:]
  if len(files) == 0:
    files.append('a.exe')

  for file in files:
    file = expand_variable(file, variables)
    if not os.path.isabs(file) and len(output_dir) > 0:
      file = os.path.join(output_dir, file)
    print(file)
    ret = util.execute_cmd(file)
    if ret != 0:
      return ret

  return 0


def main(argv):
  return parse_and_run(argv, {})


if __name__ == '__main__':
  sys.exit(main(sys.argv))