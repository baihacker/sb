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
* Put *.py in a directory and make sure the PATH environment variable contain this directory.
* Edit compilers.json and put this file in a directory, the directory can be (first match):
  * Current directory
  * %ROOTDIR%/home/config
  * %APPDATA%/../LocalLow/dcfpe
  * %APPDATA%
  * The directories in %PATH%

Install with pre-defined directory structure (recommended)
============================================
* This installation assumes you have these direcotries
  * %DEVDIR% is the dir you put all your dev softwares.
  * %ROOTDIR% is your home dir.
    * %ROOTDIR%/usr/bin this script will copy the sb system there.
    * %ROOTDIR%/home/config will contain compilers.json and a copy of setup.py.
    * %ROOTDIR%/home/config/vsc_config a copy of vsc_config
    * %ROOTDIR%/projects is assumed to be your work directory, visual studio code configuration file is initialized (.vscode).
* Steps
  * Install python 2.
  * Create directories: %DEVDIR%, %ROOTDIR%. (The sub-directories is not necessary)
    * Optional, install MinGW under %DEVDIR%. Please make sure %DEVDIR%/MinGW-w64_7.2.0/mingw64/bin exist because he script will add this path to environment variable. If this path doesn't sound good to you, please install it in another path but don't forget to edit setup.py
    * Optional, install (pe)[https://github.com/baihacker/pe]: copy the files of pe to %ROOTDIR%/usr/lib/pe and config pe if necessary. 
  * Create environment variable: DEVDIR, ROOTDIR. The value is the path of the corresponding directories.
  * Edit compilers.json according to make sure the configuration is correct.
    * The default pe compiler will use Eigen, GMP. Please remove the corresponding compile options if you don't to want to use them. Otherwise, you can put them under %ROOTDIR%/usr/lib and edit the setup.py and compilers.json.
  * Run setup.py

Usage
=====
* Command: pe++.py <your file>.
* pe++.py will try to use  {'language':'cpp','name':'mingw-pe'} to find the corresponding compiler configuration.
* dcj.py, jr.py, vc++.py are similar to pe++.py but a different filter to find the compiler configuration.
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
    * {'language':'cpp','name':'mingw-pe'}
  * vc++.py
    * {'language':'cpp','name':'vc','version':'12'}
