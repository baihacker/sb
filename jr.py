#!/usr/bin/env python
import os
import sys
import sb


def main(argv):
  return sb.parse_and_run(argv, {'compiler_spec': {'language': 'java'}})


if __name__ == '__main__':
  #if os.name == 'nt':
  #  os.system('COLOR 0A')
  sys.exit(main(sys.argv))