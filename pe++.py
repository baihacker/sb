#!/usr/bin/env python
import os
import sys
import sb


def main(argv):
  return sb.parse_and_run(
      argv, {'compiler_spec': {
          'language': 'cpp',
          'name': 'mingw64-pe'
      }})


if __name__ == '__main__':
  #if os.name == 'nt':
  #  os.system('COLOR 0A')
  print (sys.version_info)
  sys.exit(main(sys.argv))