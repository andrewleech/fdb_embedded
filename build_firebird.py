from __future__ import print_function
import os
import sys
import platform
import fileinput
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
        os.chdir(curdir)
    built_files = _built_files()
    return built_files


def build_osx(src_dir):
    # http://accountingplusplus.blogspot.com.au/2010/06/firebird-embedded-linux.html
    def _built_files():
        return [lib for lib in [os.path.join(src_dir,'gen','firebird','lib','libfbembed.dylib')] + \
          glob(os.path.join(src_dir,'gen','firebird','lib','libicu*.dylib')) if os.path.exists(lib)]

    if not len(_built_files()) > 1:
        curdir = os.path.abspath(os.curdir)
        os.chdir(os.path.join(src_dir))
        os.system("""\
        export LIBTOOLIZE=glibtoolize
        export LIBTOOL=glibtool
        ./autogen.sh
        make gen
        """)
        for line in fileinput.input("./gen/make.platform", inplace=True):
            line = line.\
                replace("-fno-weak", "").\
                replace("-mmacosx-version-min=10.6", "-mmacosx-version-min=10.7").\
                replace("LINK_OPTS:=", "LINK_OPTS:= -mmacosx-version-min=10.7").\
                replace("LD_FLAGS+=", "LD_FLAGS+= -mmacosx-version-min=10.7").\
                rstrip('\n')
            print(line)
        os.system("""\
        export LIBTOOLIZE=glibtoolize
        export LIBTOOL=glibtool
        #make gpre_boot
        #make btyacc_binary
        #make extlib
        #make external_libraries
        #make libfbstatic
        #make intl
        #make gpre_static
        make
        make libfbembed
        export LIBLOC=./gen/firebird/lib/
        export OLDPATH=/Library/Frameworks/Firebird.framework/Versions/A/Libraries

        install_name_tool -change $OLDPATH @loader_path $LIBLOC/libfbembed.dylib
        install_name_tool -change $OLDPATH/libicuuc.dylib @loader_path/libicuuc.dylib $LIBLOC/libfbembed.dylib
        install_name_tool -change $OLDPATH/libicudata.dylib @loader_path/libicudata.dylib $LIBLOC/libfbembed.dylib
        install_name_tool -change $OLDPATH/libicui18n.dylib @loader_path/libicui18n.dylib $LIBLOC/libfbembed.dylib
        install_name_tool -change $OLDPATH/libicudata.dylib @loader_path/libicudata.dylib $LIBLOC/libicuuc.dylib
        install_name_tool -change $OLDPATH/libicuuc.dylib @loader_path/libicuuc.dylib $LIBLOC/libicui18n.dylib
        install_name_tool -change $OLDPATH/libicudata.dylib @loader_path/libicudata.dylib $LIBLOC/libicui18n.dylib
        """)

        os.chdir(curdir)
    built_files = _built_files()
    return built_files


def build(src_dir):
    if sys.platform == "win32":
        return build_win32(src_dir)
    elif sys.platform == "darwin":
        return build_osx(src_dir)
    else:
        raise NotImplementedError