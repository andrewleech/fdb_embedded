#!/usr/bin/env python
"""fdb package is a set of Firebird RDBMS bindings for python.
It works on Python 2.6+ and Python 3.x.

"""
import os
import sys
import shutil
import platform
from glob import glob
from setuptools import setup, find_packages
from fdb import __version__
#import setuptools.command.build_py
from distutils.command.build import build
import distutils.cmd
import build_firebird

# Monkey-patch Distribution so it always claims to be platform-specific.
from distutils.core import Distribution
Distribution.has_ext_modules = lambda *args, **kwargs: True

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Database',
]


class BuildCommand(build):
    """Custom build command."""

    def run(self):
        self.run_command('build_firebird')
        build.run(self)

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
    install_requires=[],
    setup_requires=[],
    cmdclass={
        'build_firebird': BuildFirebirdCommand,
        'build': BuildCommand,
    },
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
)
