import os
import sys
import platform
from glob import glob

if platform.architecture()[0] == '32bit':
    PLATFORM = "win32"
elif platform.architecture()[0] == '64bit':
    PLATFORM = "amd64"
else:
    raise NotImplementedError

def build_win32(src_dir):
    def _built_files():
        return [lib for lib in [os.path.join(src_dir,'gen','Win32','fbembed.dll')] + \
          glob(os.path.join(src_dir,'gen','Win32','icu*.dll')) if os.path.exists(lib)]

    if not len(_built_files()) > 1:
        # vcvarsall = r'%LOCALAPPDATA%\Programs\Common\Microsoft\Visual C++ for Python\9.0\vcvarsall.bat'
        # if not os.path.exists(os.path.expandvars(vcvarsall)):
        #     vcvarsall = r'%COMMONPROGRAMFILES(X86)%\Microsoft\Visual C++ for Python\9.0\vcvarsall.bat'
        # if not os.path.exists(os.path.expandvars(vcvarsall)):
        #     raise Exception('"Visual C++ for Python" not found')
        # vcvars_cmd_x64 = r'call "%s" x64' %(vcvarsall)
        # vcvars_cmd_x86 = vcvars_cmd_x64 + r' && call "%s" x86' %(vcvarsall) # run vcvars_cmd_x64 first to get vcbuild.exe
        # vcvars_cmd = vcvars_cmd_x86 if PLATFORM == 'win32' else vcvars_cmd_x64
        curdir = os.path.abspath(os.curdir)
        os.chdir(os.path.join(src_dir,'builds','win32'))
        os.system("""\
        set FB_PROCESSOR_ARCHITECTURE=x86&&\
        set VS100COMNTOOLS=&&\
        call make_icu.bat &&\
        call make_boot.bat &&\
        call make_all.bat
        """)
        #TODO move compile embed files somewhere
        os.chdir(curdir)
    built_files = _built_files()
    return built_files


def build_posix(src_dir):
    # http://accountingplusplus.blogspot.com.au/2010/06/firebird-embedded-linux.html
    raise NotImplementedError


def build(src_dir):
    if sys.platform == "win32":
        return build_win32(src_dir)
    elif sys.platform == "darwin":
        return build_posix(src_dir)