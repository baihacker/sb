import os
import sys
import shutil
import zipfile
import json
import time
import subprocess
import sb

def main(argv):
  output = ''
  files = []
  is_debug = False

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
    else:
      files.append(argv[i])
      i += 1

  sb.compile(files, output, {'language':'cpp','name':'mingw-pe'}, is_debug)

if __name__ == '__main__':
  # parse cmdline
  main(sys.argv)