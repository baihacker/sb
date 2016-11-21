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
    elif argv[i].lower() == '-r':
      run = True
      i += 1
    else:
      files.append(argv[i])
      i += 1

  compile_cmd, run_cmd = sb.create_commands(files, output, {'language':'java'}, is_debug)
  if compile_cmd() == 0 and run == True:
    run_cmd()

if __name__ == '__main__':
  # parse cmdline
  main(sys.argv)