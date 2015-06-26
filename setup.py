#!/usr/bin/env python
"""fdb package is a set of Firebird RDBMS bindings for python.
It works on Python 2.6+ and Python 3.x.

"""
import os
import sys
import shutil
from glob import glob
from setuptools import setup, find_packages
from fdb.fbcore import __version__
import setuptools.command.build_py
import distutils.cmd
from distutils.command.build import build
from setuptools.command.install import install

import build_firebird

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Database',
]

## CFFI build framework
#  https://caremad.io/2014/11/distributing-a-cffi-project/

SETUP_REQUIRES_ERROR = (
    "Requested setup command that needs 'setup_requires' while command line "
    "arguments implied a side effect free command or option."
)

NO_SETUP_REQUIRES_ARGUMENTS = [
    "-h", "--help",
    "-n", "--dry-run",
    "-q", "--quiet",
    "-v", "--verbose",
    "-v", "--version",
    "--author",
    "--author-email",
    "--classifiers",
    "--contact",
    "--contact-email",
    "--description",
    "--egg-base",
    "--fullname",
    "--help-commands",
    "--keywords",
    "--licence",
    "--license",
    "--long-description",
    "--maintainer",
    "--maintainer-email",
    "--name",
    "--no-user-cfg",
    "--obsoletes",
    "--platforms",
    "--provides",
    "--requires",
    "--url",
    "clean",
    "egg_info",
    "register",
    "sdist",
    "upload",
]

def get_ext_modules():
    from fdb import ibase_cffi_build
    return [ibase_cffi_build.ffi.distutils_extension()]


class CFFIBuild(build):
    def finalize_options(self):
        self.distribution.ext_modules = get_ext_modules()
        build.finalize_options(self)


class CFFIInstall(install):
    def finalize_options(self):
        self.distribution.ext_modules = get_ext_modules()
        install.finalize_options(self)


class DummyCFFIBuild(build):
    def run(self):
        raise RuntimeError(SETUP_REQUIRES_ERROR)


class DummyCFFIInstall(install):
    def run(self):
        raise RuntimeError(SETUP_REQUIRES_ERROR)


def keywords_with_side_effects(argv):
    def is_short_option(argument):
        """Check whether a command line argument is a short option."""
        return len(argument) >= 2 and argument[0] == '-' and argument[1] != '-'

    def expand_short_options(argument):
        """Expand combined short options into canonical short options."""
        return ('-' + char for char in argument[1:])

    def argument_without_setup_requirements(argv, i):
        """Check whether a command line argument needs setup requirements."""
        if argv[i] in NO_SETUP_REQUIRES_ARGUMENTS:
            # Simple case: An argument which is either an option or a command
            # which doesn't need setup requirements.
            return True
        elif (is_short_option(argv[i]) and
              all(option in NO_SETUP_REQUIRES_ARGUMENTS
                  for option in expand_short_options(argv[i]))):
            # Not so simple case: Combined short options none of which need
            # setup requirements.
            return True
        elif argv[i - 1:i] == ['--egg-base']:
            # Tricky case: --egg-info takes an argument which should not make
            # us use setup_requires (defeating the purpose of this code).
            return True
        else:
            return False

    if all(argument_without_setup_requirements(argv, i)
           for i in range(1, len(argv))):
        return {
            "cmdclass": {
                "build": DummyCFFIBuild,
                "install": DummyCFFIInstall,
            }
        }
    else:
        return {
            "setup_requires": ["cffi"],
            "cmdclass": {
                'build_firebird': BuildFirebirdCommand,
                'build_py': BuildPyCommand,
                "build": CFFIBuild,
                "install": CFFIInstall,
            }
        }


## Firebird build framework

class BuildPyCommand(setuptools.command.build_py.build_py):
    """Custom build command."""

    def run(self):
        self.run_command('build_firebird')
        setuptools.command.build_py.build_py.run(self)

class BuildFirebirdCommand(distutils.cmd.Command):
    """A custom command to build firebird embedded libraries."""

    description = 'build firebird embedded libraries'
    user_options = [
        # The format is (long option, short option, description).
        ('firebird-source=', None, 'path to firebird source tree'),
    ]
    def initialize_options(self):
        """Set default values for options."""
        # Each user option must be listed here with their default value.
        self.firebird_source = os.path.join(os.path.dirname(__file__), 'firebird')

    def finalize_options(self):
        """Post-process options."""
        assert os.path.exists(self.firebird_source), (
              'Firebird source %s does not exist.' % self.firebird_source)

    def run(self):
        """Run command."""
        # data_files = build_firebird.build(self.firebird_source)
        # if not self.distribution.data_files:
        #     self.distribution.data_files = []
        # self.distribution.data_files.append(('',data_files))

        package_data = build_firebird.build(self.firebird_source)
        libdir = os.path.join(".","fdb","lib")
        if not os.path.exists(libdir):
            os.makedirs(libdir)
        [shutil.copy(lib, libdir) for lib in package_data]
        self.distribution.package_data['fdb'] += [os.path.relpath(lib, os.path.join(".","fdb")) for lib in glob(os.path.join(libdir, '*'))]

setup(name='fdb', 
        version=__version__,
        description = 'Firebird RDBMS bindings for Python.', 
        url='http://www.firebirdsql.org/en/python-devel-status/',
        classifiers=classifiers,
        keywords=['Firebird'],
        license='BSD',
        author='Pavel Cisar',
        author_email='pcisar@users.sourceforge.net',
        long_description=__doc__,
    packages=find_packages(exclude=['ez_setup']),
    test_suite='nose.collector',
    include_package_data=False,
    package_data={'fdb': ['*.txt'],
                  'test':'fbtest.fdb'},
    #message_extractors={'fdb': [
            #('**.py', 'python', None),
            #('public/**', 'ignore', None)]},
    zip_safe=False,
    entry_points="""
    """,
    # setup_requires=["cffi>=1.0.0"],
    # cffi_modules=["fdb/ibase_cffi_build.py:ffi"],
    # install_requires=["cffi>=1.0.0"],
    **keywords_with_side_effects(sys.argv)
)
