from __future__ import print_function
import os
import sys
import shutil
import platform
import fileinput
from glob import glob

FIREBIRD_VERSION = "2.5.4"

# From http://www.firebirdsql.org/en/firebird-2-5/
URLS = {
    "source"        : "http://sourceforge.net/projects/firebird/files/firebird/2.5.4-Release/Firebird-2.5.4.26856-0.tar.bz2",
    "win32_x86"   : "http://sourceforge.net/projects/firebird/files/firebird-win32/2.5.4-Release/Firebird-2.5.4.26856-0_Win32_embed.zip",
    "win32_amd64"   : "http://sourceforge.net/projects/firebird/files/firebird-win64/2.5.4-Release/Firebird-2.5.4.26856-0_x64_embed.zip",
    "linux_x86"     : "http://sourceforge.net/projects/firebird/files/firebird-linux-i386/2.5.4-Release/FirebirdCS-2.5.4.26856-0.i686.tar.gz",
    "linux_amd64"   : "http://sourceforge.net/projects/firebird/files/firebird-linux-amd64/2.5.4-Release/FirebirdCS-2.5.4.26856-0.amd64.tar.gz",
    "osx_lipo"      : "http://sourceforge.net/projects/firebird/files/firebird-MacOS-X_darwin/2.5.4-Release/FirebirdCS-2.5.4-26856-lipo-x86_64.pkg.zip"
}

if platform.architecture()[0] == '32bit':
    PLATFORM = "x86"
elif platform.architecture()[0] == '64bit':
    PLATFORM = "amd64"
else:
    raise NotImplementedError

import httplib
import socket
import ssl
import urllib2

def connect(self):
    "Connect to a host on a given (SSL) port."
    sock = socket.create_connection((self.host, self.port),
                                    self.timeout, self.source_address)
    if self._tunnel_host:
        self.sock = sock
        self._tunnel()
    self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_TLSv1)

httplib.HTTPSConnection.connect = connect


def download_file(url, dest):
    import requests
    if not os.path.exists(dest):
        os.makedirs(dest)
    file_name = os.path.join(dest,url.split('/')[-1])
    response = requests.get(url, stream=True)
    response.raise_for_status()
    meta = response.headers
    file_size = int(meta.get("Content-Length", -1))
    if os.path.exists(file_name) and os.path.getsize(file_name) == file_size:
        print("Using previously downloaded: %s" % (file_name))
    else:
        with open(file_name, 'wb') as fp:
            print("Downloading: %s %s KB" % (file_name, file_size/1024))

            file_size_dl = 0
            block_sz = 8192
            for block in response.iter_content(block_sz):
                if not block:
                    break
                file_size_dl += len(block)
                fp.write(block)

                percent = file_size_dl * 100. / file_size
                status = "\r%10d  [%3.2f%%] " % (file_size_dl, percent)
                status = status + "#"*(int(percent)+1)
                print(status, end="")
            print(" Done.")
    return file_name

def _shutil_remove_readonly(func, path, excinfo):
    "Clear the readonly bit and reattempt the removal"
    import stat
    os.chmod(path, stat.S_IWUSR)
    func(path)

def extract(filename):
    folder, extension = os.path.splitext(filename)
    if extension.endswith('zip'):
        import zipfile
        if os.path.exists(folder):
            shutil.rmtree(folder, onerror=_shutil_remove_readonly)
        os.makedirs(folder)
        zip = zipfile.ZipFile(filename, 'r')
        zip.extractall(folder)
    else:
        import tarfile
        if os.path.exists(folder):
            shutil.rmtree(folder, onerror=_shutil_remove_readonly)
        os.makedirs(folder)
        tar = tarfile.open(filename, "r")
        tar.extractall(folder)
    return folder

def download_source(build_dir):
    archive = download_file(URLS['source'], build_dir)
    folder = extract(archive)
    return folder


def download_win32(output_dir):
    arch = "win32_%s" % PLATFORM
    if arch in URLS:
        archive = download_file(URLS[arch], output_dir)
        folder = extract(archive)
        libs = glob(os.path.join(folder,'*.dll'))
        return libs

def download_osx(output_dir):
    archive = download_file(URLS['osx_lipo'], output_dir)
    folder = extract(archive)

    inner_archive = None
    if folder.endswith('pkg'): # osx
        for root, dirs, names in os.walk(folder):
            if "Archive.pax.gz" in names:
                inner_archive = os.path.join(root, 'Archive.pax.gz')
                break
    if not inner_archive:
        raise OSError("Required library missing from download: 'Archive.pax.gz'" )

    curdir = os.path.abspath(os.curdir)
    os.chdir(folder)
    os.system("gzip -cd {pkg} |pax -r".format(pkg=os.path.relpath(inner_archive, folder)))
    os.chdir(curdir)

    libfbembed = os.path.join(folder,'Firebird.framework','Versions','A','Libraries','libfbembed.dylib')
    if not os.path.exists(libfbembed):
        libfbembed = os.path.join(folder,'Firebird.framework','Versions','A','Libraries','libfbclient.dylib')
        if not os.path.exists(libfbembed):
            raise OSError("Required library missing from download: " + libfbembed)
    # add relative path searching for dependent libraries
    os.system("""\
    export LIBLOC={folder}/Firebird.framework/Versions/A/Libraries
    export OLDPATH=/Library/Frameworks/Firebird.framework/Versions/A/Libraries

    install_name_tool -change $OLDPATH @loader_path {libfbembed}
    install_name_tool -change $OLDPATH/libicuuc.dylib @loader_path/libicuuc.dylib {libfbembed}
    install_name_tool -change $OLDPATH/libicudata.dylib @loader_path/libicudata.dylib {libfbembed}
    install_name_tool -change $OLDPATH/libicui18n.dylib @loader_path/libicui18n.dylib {libfbembed}
    install_name_tool -change $OLDPATH/libicudata.dylib @loader_path/libicudata.dylib $LIBLOC/libicuuc.dylib
    install_name_tool -change $OLDPATH/libicuuc.dylib @loader_path/libicuuc.dylib $LIBLOC/libicui18n.dylib
    install_name_tool -change $OLDPATH/libicudata.dylib @loader_path/libicudata.dylib $LIBLOC/libicui18n.dylib
    """.format(folder=folder, libfbembed=libfbembed))

    libs = glob(os.path.join(folder,'Firebird.framework','Versions','A','Libraries','*.dylib'))
    return libs

def download_linux(output_dir):
    arch = "linux_%s" % PLATFORM
    if arch in URLS:
        archive = download_file(URLS[arch], output_dir)
        folder = extract(archive)
        inner_archive = None
        for root, dirs, names in os.walk(folder):
            if 'buildroot.tar.gz' in names:
                inner_archive = os.path.join(root, 'buildroot.tar.gz')
                break
        if not inner_archive:
            raise OSError("Required library missing from download: 'buildroot.tar.gz'" )
        buildroot = extract(inner_archive)
        libs = glob(os.path.join(buildroot,'opt','firebird','lib','*.so'))

        ## add relative path searching for dependent libraries
        # https://alioth.debian.org/frs/?group_id=31052
        from distutils.spawn import find_executable
        chrpath = find_executable('chrpath')
        if not chrpath:
            chrpath_src = download_file("https://alioth.debian.org/frs/download.php/file/3979/chrpath-0.16.tar.gz", output_dir)
            chrpath_src_dir = extract(chrpath_src)
            if len(os.listdir(chrpath_src_dir)) == 1: # extra subdir
                chrpath_src_dir = os.path.join(chrpath_src_dir,os.listdir(chrpath_src_dir)[0])
            curdir = os.path.abspath(os.curdir)
            os.chdir(chrpath_src_dir)
            os.system("""\
            sh configure
            make
            """)
            os.chdir(curdir)
            chrpath = find_executable('chrpath', chrpath_src_dir)
        if not chrpath:
            raise OSError("chrpath utility not available, please install from package manager")
        for lib in libs:
            os.system("""\
            CURRENT=`chrpath -l {lib}`
            chrpath -r '$$ORIGIN:$CURRENT' {lib}
            """.format(lib=lib))

        return libs

def build_win32(src_dir):
    def _built_files():
        return [lib for lib in [os.path.join(src_dir,'gen','Win32','fbembed.dll')] + \
          glob(os.path.join(src_dir,'gen','Win32','icu*.dll')) if os.path.exists(lib)]

    if not len(_built_files()) > 1:
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
    if len(os.listdir(src_dir)) == 1:
        src_dir = os.path.join(src_dir,os.listdir(src_dir)[0])

    def _built_files():
        return [lib for lib in [os.path.join(src_dir,'gen','firebird','lib','libfbembed.dylib')] + \
          glob(os.path.join(src_dir,'gen','firebird','lib','libicu*.dylib')) if os.path.exists(lib)]

    if not len(_built_files()) > 1:
        curdir = os.path.abspath(os.curdir)
        os.chdir(os.path.join(src_dir))
        os.system("""\
        export LIBTOOLIZE=glibtoolize
        export LIBTOOL=glibtool
        sh autogen.sh
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
        export LIBLOC=gen/firebird/lib/
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


def build_linux(src_dir):
    def _built_files():
        return glob(os.path.join(src_dir,'gen','firebird','lib','libfbembed.so*')) + \
               glob(os.path.join(src_dir,'gen','firebird','lib','libicu*.so*'))

    if not len(_built_files()) > 1:
        curdir = os.path.abspath(os.curdir)
        os.chdir(os.path.join(src_dir))
        os.system("""\
        sh autogen.sh
        make gen
        """)
        with open("./gen/make.platform", "a") as make_platform:
            make_platform.write("\nLDFLAGS+=-Wl,-rpath,'$$ORIGIN'")
        os.system("""\
        make
        make libfbembed
        """)

        os.chdir(curdir)
    built_files = _built_files()
    return built_files


def build(build_dir):
    platform = sys.platform
    if platform == "win32":
        ret = download_win32(build_dir)
        if not ret:
            src_dir = download_source(build_dir)
            ret = build_win32(src_dir)
    elif platform == "darwin":
        ret = download_osx(build_dir)
        if not ret:
            src_dir = download_source(build_dir)
            ret = build_osx(src_dir)
    elif platform.startswith("linux"):
        ret = download_linux(build_dir)
        if not ret:
            src_dir = download_source(build_dir)
            ret = build_linux(src_dir)
    else:
        raise NotImplementedError
    return ret