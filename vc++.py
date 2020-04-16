#!/usr/bin/env python
import os
import sys
import sb


def main(argv):
  sb.parse_and_run(
      argv, {
          'compiler_spec': {
              'language': 'cpp',
              'name': 'vc',
              'version': '14',
              'arch': 'x64'
          }
      })


if __name__ == '__main__':
  if os.name == 'nt':
    os.system('COLOR 0A')
  main(sys.argv)