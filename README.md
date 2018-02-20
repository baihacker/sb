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

Installion
==========
* Install python 2.
* Put *.py in a directory and make sure the PATH environment variable contain this directory.
* Edit compilers.json and put this file in a directory, the directory can be (first match):
  * Current directory
  * %ROOTDIR%/home/config
  * %APPDATA%/../LocalLow/dcfpe
  * %APPDATA%
  * The directories in %PATH%

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
