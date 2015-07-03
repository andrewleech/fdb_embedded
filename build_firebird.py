from __future__ import print_function
import os
import sys
import ssl
import shutil
import socket
import httplib
import platform
import fileinput
from glob import glob
from distutils.dir_util import copy_tree, remove_tree
from setuptools.command.build_ext import build_ext
from distutils.dir_util import copy_tree

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

# Monkey-patch Distribution so it always claims to be platform-specific.
from distutils.core import Distribution
Distribution.has_ext_modules = lambda s, *args, **kwargs: True #   lambda s, *args, **kwargs: s.ext_modules = ["dummy"] if not s.ext_modules else s.ext_modules
Distribution.is_pure = lambda *args, **kwargs: False

## SSL wrapper
def connect(self):
    "Connect to a host on a given (SSL) port."
    sock = socket.create_connection((self.host, self.port),
                                    self.timeout, self.source_address)
    if self._tunnel_host:
        self.sock = sock
        self._tunnel()
    self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_TLSv1)

httplib.HTTPSConnection.connect = connect

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    def __getattr__(self, attr):
        return self.get(attr)
    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__



## We need to pass something testable to setup(ext_modules=<value>) to trigger pure/plat decision in distutils.command.build.finalize_options()
ext_modules = [dotdict(name='firebird')]

class BuildFirebirdCommand(build_ext):
    """A custom command to build firebird embedded libraries."""

    description = 'build firebird embedded libraries'
    user_options = [
        # The format is (long option, short option, description).
        ('firebird-source=', None, 'path to firebird source tree'),
    ]
    def initialize_options(self):
        """Set default values for options."""
        # Each user option must be listed here with their default value.
        self.build_lib = None
        self.firebird_staging = os.path.join(os.path.dirname(__file__), 'build', 'firebird')
        if not os.path.exists(self.firebird_staging):
            os.makedirs(self.firebird_staging)
        self.outfiles = []

    def finalize_options(self):
        """Post-process options."""
        self.set_undefined_options('build',
                           ('build_lib', 'build_lib'))
        assert os.path.exists(self.firebird_staging), (
              'Firebird source %s does not exist.' % self.firebird_staging)

    def run(self):
        """Run command."""
        libraries = firebird_libraries(self.firebird_staging)

        ## Copy firebird libraries into module in-place
        libdir = os.path.join('fdb_embedded',"lib")
        if not os.path.exists(libdir):
            os.makedirs(libdir)
        outfiles = []
        for lib in libraries:
            dest = os.path.join(libdir, os.path.basename(lib))
            if os.path.isdir(lib):
                outfiles.extend( copy_tree(lib, dest, preserve_symlinks=True, update=True) )
            else:
                shutil.copy(lib, libdir)
                outfiles.append(dest)
        self.outfiles = outfiles

        ## Copy firebird libraries into build dir to be included in binary dist
        copy_tree(libdir, os.path.join(self.build_lib, libdir), preserve_symlinks=True, update=True)

        ## Update ext_modules list for use later on in install_egg_info
        self.distribution.ext_modules = [(name, None) for name in self.outfiles]

    def get_source_files(self):
        return []


if platform.architecture()[0] == '32bit':
    PLATFORM = "x86"
elif platform.architecture()[0] == '64bit':
    PLATFORM = "amd64"
else:
    raise NotImplementedError



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

# def rmdir(path):
#     print("Removing: %s" % path)
#     if sys.platform == "win32":
#         os.system("RMDIR /s /q %s" % os.path.normpath(path))
#     else:
#         os.system("rm -rf %s" % path)

def extract(filename):
    folder, extension = os.path.splitext(filename)
    if extension.endswith('zip'):
        import zipfile
        if os.path.exists(folder):
            remove_tree(folder)
        os.makedirs(folder)
        zip = zipfile.ZipFile(filename, 'r')
        zip.extractall(folder)
    else:
        import tarfile
        if os.path.exists(folder):
            remove_tree(folder)
        os.makedirs(folder)
        tar = tarfile.open(filename, "r")
        tar.extractall(folder)
    return folder

def download_source(build_dir):
    archive = download_file(URLS['source'], build_dir)
    folder = extract(archive)
    return folder


def download_win32(output_dir):
    libs = []
    arch = "win32_%s" % PLATFORM
    if arch in URLS:
        archive = download_file(URLS[arch], output_dir)
        folder = extract(archive)
        libs = glob(os.path.join(folder,'*.dll'))
    [print("downloaded %s lib: %s" % (arch,lib)) for lib in libs]
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

    framework = os.path.join(folder,'Firebird.framework')
    if not os.path.exists(framework):
        raise OSError("Required library missing from download: " + framework)
    # add relative path searching for dependent libraries
    os.system("""\
    export OLDPATH=/Library/Frameworks/Firebird.framework/Versions/A/Libraries
    install_name_tool -change $OLDPATH/libicuuc.dylib   @loader_path/Libraries/libicuuc.dylib   {framework}/Firebird
    install_name_tool -change $OLDPATH/libicudata.dylib @loader_path/Libraries/libicudata.dylib {framework}/Firebird
    install_name_tool -change $OLDPATH/libicui18n.dylib @loader_path/Libraries/libicui18n.dylib {framework}/Firebird
    install_name_tool -change $OLDPATH/libicudata.dylib @loader_path/libicudata.dylib           {framework}/Libraries/libicuuc.dylib
    install_name_tool -change $OLDPATH/libicuuc.dylib   @loader_path/libicuuc.dylib             {framework}/Libraries/libicui18n.dylib
    install_name_tool -change $OLDPATH/libicudata.dylib @loader_path/libicudata.dylib           {framework}/Libraries/libicui18n.dylib
    """.format(folder=folder, framework=framework))

    libs = [framework]
    [print("downloaded osx lib: " + lib) for lib in libs]
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

        [print("downloaded linux lib: " + lib) for lib in libs]
        return libs

def build_win32(src_dir):
    #TODO amd64 support
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
    [print("built win32 lib: " + lib) for lib in built_files]
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
        cp builds/posix/prefix.darwin_x86_64 gen/make.platform
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
    [print("built osx lib: " + lib) for lib in built_files]
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
    [print("built linux lib: " + lib) for lib in built_files]
    return built_files


def firebird_libraries(build_dir):
    ret = None
    platform = sys.platform
    if platform == "win32":
        try:
            ret = download_win32(build_dir)
        except OSError as ex: print("Error in downloaded package: "+ str(ex))
        if not ret:
            src_dir = download_source(build_dir)
            ret = build_win32(src_dir)
    elif platform == "darwin":
        try:
           ret = download_osx(build_dir)
        except OSError as ex: print("Error in downloaded package: "+ str(ex))
        if not ret:
            src_dir = download_source(build_dir)
            ret = build_osx(src_dir)
    elif platform.startswith("linux"):
        try:
            ret = download_linux(build_dir)
        except OSError as ex: print("Error in downloaded package: "+ str(ex))
        if not ret:
            src_dir = download_source(build_dir)
            ret = build_linux(src_dir)
    else:
        raise NotImplementedError
    return ret