import os
import sys
import shutil
import zipfile
import json
import time
import subprocess
import sb

def main(argv):
  sb.parse_and_run(argv, {'compiler_spec': {'language':'cpp','name':'vc','version':'14','arch':'x64'}})

if __name__ == '__main__':
  # parse cmdline
  os.system('COLOR 0A')
  main(sys.argv)