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
from fdb_embedded import __version__
from setuptools.command import build_ext
from distutils.command.build import build
import distutils.cmd
import build_firebird

# Monkey-patch Distribution so it always claims to be platform-specific.
from distutils.core import Distribution
Distribution.has_ext_modules = lambda *args, **kwargs: True
Distribution.is_pure = lambda *args, **kwargs: False

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Database',
]


# class BuildCommand(build_ext):
#     """Custom build command."""
#
#     def run(self):
#         self.run_command('build_firebird')
#         build.run(self)

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
        self.firebird_source = os.path.join(os.path.dirname(__file__), 'build', 'firebird')
        if not os.path.exists(self.firebird_source):
            os.makedirs(self.firebird_source)
        self.data_files = []

    # def __getattr__(self, item):
    #     return distutils.cmd.Command.__getattr__(self, item)

    def finalize_options(self):
        """Post-process options."""
        assert os.path.exists(self.firebird_source), (
              'Firebird source %s does not exist.' % self.firebird_source)

    def run(self):
        """Run command."""
        package_data = build_firebird.build(self.firebird_source)
        libdir = os.path.join("fdb_embedded","lib")
        if not os.path.exists(libdir):
            os.makedirs(libdir)
        data_files = []
        for lib in package_data:
            dest = os.path.join(libdir, lib)
            if os.path.isdir(lib):
                if os.path.exists(dest):
                    shutil.rmtree(dest)
                shutil.copytree(lib, dest)
                for root, dirname, filename in os.walk(dest):
                    data_files.append(os.path.join(root, filename))
            else:
                shutil.copy(lib, libdir)
                data_files.append(os.path.join(libdir, os.path.basename(lib)))
        self.data_files = data_files
        #self.distribution.package_data['fdb_embedded'] += data_files

    def get_source_files(self):
        return self.data_files


setup(name='fdb_embedded',
    version=__version__,
    description = 'Firebird RDBMS bindings for Python with built in fb embedded server.',
    url = "https://github.com/andrewleech/fdb_embedded",
    classifiers=classifiers,
    keywords=['Firebird'],
    license='BSD',
    author='Andrew Leech',
    author_email='andrew@alelec.net',
    long_description=__doc__,
    install_requires=['requests'],
    setup_requires=[],
    cmdclass={
        'build_firebird': BuildFirebirdCommand,
        'build_ext': BuildFirebirdCommand,
    },
    ext_modules=[('firebird', 'dummy')],
    packages=find_packages(exclude=['ez_setup']),
    test_suite='nose.collector',
    include_package_data=False,
    package_data={'fdb_embedded': ['*.txt'],
                  'test':'fbtest.fdb'},
    #message_extractors={'fdb_embedded': [
            #('**.py', 'python', None),
            #('public/**', 'ignore', None)]},
    zip_safe=False,
    entry_points="""
    """,
)
