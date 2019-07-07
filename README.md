# sb
A very simple building system

## Features
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

## Installation
### Simple installation
* Install python 2.
* Put *.py and *.bat in a directory and make sure the PATH environment variable contain this directory.
* Edit compilers.json and put this file in a directory, the directory can be (first match):
  * Current directory
  * %HOMEDIR%/config
  * %ROOTDIR%/config
  * %APPDATA%/../LocalLow/dcfpe
  * %APPDATA%
  * The directories in %PATH%

### Install with pre-defined directory structures (recommended)
This installation uses this directory structure:
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

#### Install on windows

  * Prepare
    * Install python 2.
    * Make sure environment variable ROOTDIR and HOMEDIR are valid directory path. (No need to create the sub-directories of ROOTDIR or HOMEDIR and they will be created automatically if not exist)
    * Make sure DEVPATH is a part of PATH, i.e PATH=%DEVPATH%;...
    * Check other configurations.
    * Note: Open and close the environment setting dialog to let the new created/updated environment variables take effect.
  * Install
    * Run cmd with administrator permission.
    * Enter this dir.
    * Execute: python setup.py
  * After installing sb
    * Open and close the environment setting dialog to let the new created/updated environment variables take effect.

#### Install on linux

  * Prepare
    * Install python 2.
    * Make sure environment variable ROOTDIR and HOMEDIR are valid directory path. (No need to create the sub-directories of ROOTDIR OR HOMEDIR and they will be created automatically if not exist)
    * Check other configurations
    * Append the following code (please modify `<home dir> and <root dir>`) to ~/.bashrc
```bash
        export HOMEDIR=<home dir>
        export ROOTDIR=<root dir>

        if [ -f ~/.sbrc ]; then
         . ~/.sbrc
        fi

        export PATH=$DEVPATH:$PATH
```

  * Install
    * Open terminal.
    * Enter this dir.
    * Execute: python ./setup.py

#### Other configurations

  * [Optional, Windows] install MinGW under %ROOTDIR%/app/DevSoft.
    * Please make sure %ROOTDIR%/app/DevSoft/MinGW-x86_64-8.1.0-posix-seh-rt_v6-rev0/mingw64/bin exist because this script will add that path to environment variable list.
    * If the path doesn't sound good to you, please install it in another path but don't forget to edit setup.py
  * Configure [pe](https://github.com/baihacker/pe)
    * This script will install [pe](https://github.com/baihacker/pe) to %HOMEDIR%/usr/include/pe and configure it automatically.
    * Please configure it when necessary
  * Configure compiler compilers.json.
    * [Windows] The default pe compiler will use Eigen, GMP. Please remove the corresponding compile options if you don't to want to use them. Otherwise, you can put them under %HOMEDIR%/usr/lib and edit the setup.py and compilers.json.

## Usage
* Command
  * Windows: pe++.py `<source file>`.
    * pe++ `<source file>` is available but it is not recommended.
  * Linux: pe++ `<source file>`.
  * pe++.py uses {'language':'cpp','name':'mingw64-pe'} to find the corresponding compiler.
  * dcj.py, jr.py, vc++.py, clang++ are similar to pe++.py but a different compiler spec to find the compiler, please see copmiler spec list.
  * pe++ (linux) will reuse pe++.py with another copmiler name gcc-pe.
* options
  * -o `<output file name>`
    * Specify the output file name. (Default = empty string and determined by compilers)
  * -debug
    * Enable debug mode.
  * -release
    * Enable release mode. (Default)
  * -r
    * Run the application after compiling your source code successfully. (Not enabled by default)
  * -l
    * specify the language
  * -n
    * specify the name field in compiler spec.
  * -a
    * specify the arch field in compiler spec.
  * --
    * all the options after -- will be appended to the compiler command.
* Compiler spec list
  * clang++.py
    * {'language':'cpp','name':'clang-pe'}
  * dcj.py
    * {'language':'cpp','name':'dcj'}
  * jr.py
    * {'language':'java'}
  * pe++.py
    * {'language':'cpp','name':'mingw64-pe'}
  * vc++.py
    * {'language':'cpp','name':'vc','version':'14','arch':'x64'}
