# sb
A very simple building system

Features
========
* Support nearly all kinds of compilers (easy to extend to other compiler/languages):
  * mingw: c, c++
  * tdm-mingw: c, c++
  * clang: c, c++
  * dcj: c++
  * python interpreter: python
  * go compiler: go
  * java compiler: java
  * scala interpreter: scala
  * ghc: haskell
  * vc: c, c++
* Use variable to help configure compilers.
* Work with [win_toolchain_2013e](http://yun.baidu.com/share/link?shareid=2799405881&uk=2684621311) without installing vs2013.

Installation
==========
* Install python 2.
* Put *.py and *.bat in a directory and make sure the PATH environment variable contain this directory.
* Edit compilers.json and put this file in a directory, the directory can be (first match):
  * Current directory
  * %HOMEDIR%/config
  * %ROOTDIR%/config
  * %APPDATA%/../LocalLow/dcfpe
  * %APPDATA%
  * The directories in %PATH%

Install with pre-defined directory structure (recommended)
============================================
* This installation uses this directory structure:
  * %ROOTDIR% is the root directory.
    * %ROOTDIR%/app the directory to install applications.
    * %ROOTDIR%/app/DevSoft development related software.
    * %ROOTDIR%/app/MathsSoft maths related software.
    * %ROOTDIR%/projects your work directory, visual studio code configuration file is initialized there (.vscode).
    * %ROOTDIR%/devices device dependent data. e.g. If you have two PCs, each PC has its own directory.
  * %HOMEDIR% is the home directory.
    * %HOMEDIR%/config will contain compilers.json and a copy of setup.py.
    * %HOMEDIR%/config/vsc_config a copy of vsc_config.
    * %HOMEDIR%/usr/bin/sb this script will copy the **sb system** there.
* Steps
  * Install python 2.
  * Create the root dir and add set the value of environment variable ROOTDIR to the dir created. (No need to create the sub-directories of ROOTDIR and they will be created automatically if not exist)
  * For HOMEDIR, the step is similar to ROOTDIR.
  * Optional, install MinGW under %ROOTDIR%/app/DevSoft. Please make sure %ROOTDIR%/app/DevSoft/MinGW-x86_64-8.1.0-posix-seh-rt_v6-rev0/mingw64/bin exist because this script will add that path to environment variable list. If the path doesn't sound good to you, please install it in another path but don't forget to edit setup.py
  * Optional, install [pe](https://github.com/baihacker/pe): copy the files of pe to %HOMEDIR%/usr/include/pe and **config** pe if necessary (see [pe](https://github.com/baihacker/pe) for how to config it).
  * Configure compilers.json.
    * The default pe compiler will use Eigen, GMP. Please remove the corresponding compile options if you don't to want to use them. Otherwise, you can put them under %HOMEDIR%/usr/lib and edit the setup.py and compilers.json.
  * Run setup.py

Usage
=====
* Command: pe++.py <your file>.
* pe++.py will try to use  {'language':'cpp','name':'mingw64-pe'} to find the corresponding compiler configuration.
* dcj.py, jr.py, vc++.py, clang++ are similar to pe++.py but a different filter to find the compiler configuration.
* options
  * -o <output file name>
    * Specify the output file name. (Default = empty string and determined by compilers)
  * -debug
    * Enable debug mode.
  * -release
    * Enable release mode. (Default)
  * -r
    * Run the application after compiling your source code successfully. (Not enabled by default)
* Configuration list
  * dcj.py
    * {'language':'cpp','name':'dcj'}
  * jr.py
    * {'language':'java'}
  * pe++.py
    * {'language':'cpp','name':'mingw64-pe'}
  * vc++.py
    * {'language':'cpp','name':'vc','version':'14'}
  * clang++.py
    * {'language':'cpp','name':'clang-pe'}
