#!/usr/bin/env python
# coding: utf-8

"""
    distutils setup
    ~~~~~~~~~~~~~~~

    :copyleft: 2010-2011 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import os
import sys

from setuptools import setup, find_packages
from django_processinfo import VERSION_STRING


PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))


def get_authors():
    authors = []
    try:
        f = file(os.path.join(PACKAGE_ROOT, "AUTHORS"), "r")
    except Exception, err:
        return ["[Error reading AUTHORS file: %s]" % err]
    for line in f:
        if line.startswith('*'):
            authors.append(line[1:].strip())
    f.close()
    return ", ".join(authors)


def get_long_description():
    """
    returns README.creole as ReStructuredText.
    Code from:
        https://code.google.com/p/python-creole/wiki/UseInSetup
    """
    desc_creole = ""
    raise_errors = "register" in sys.argv or "sdist" in sys.argv or "--long-description" in sys.argv
    try:
        f = file(os.path.join(PACKAGE_ROOT, "README.creole"), "r")
        desc_creole = f.read()
        f.close()
        desc_creole = unicode(desc_creole, 'utf-8').strip()

        try:
            from creole import creole2html, html2rest
        except ImportError:
            etype, evalue, etb = sys.exc_info()
            evalue = etype("%s - Please install python-creole, e.g.: pip install python-creole" % evalue)
            raise etype, evalue, etb

        desc_html = creole2html(desc_creole)
        long_description = html2rest(desc_html)
    except Exception, err:
        if raise_errors:
            raise
        # Don't raise the error e.g. in ./setup install process
        long_description = "[Error: %s]\n%s" % (err, desc_creole)

    if raise_errors:
        # Try if created ReSt code can be convertet into html
        from creole.rest2html.clean_writer import rest2html
        rest2html(long_description)

    return long_description


setup(
    name='django-processinfo',
    version=VERSION_STRING,
    description='django-processinfo is a Django application to collect information about the running server processes.',
    long_description=get_long_description(),
    author=get_authors(),
    maintainer="Jens Diemer",
    maintainer_email="django-processinfo@jensdiemer.de",
    url="https://github.com/jedie/django-processinfo",
    packages=find_packages(),
    include_package_data=True, # include files specified by MANIFEST.in
    install_requires=[
        "Django>=1.3,<1.4", # Django v1.3.x
    ],
    zip_safe=False,
    classifiers=[
        "Development Status :: 1 - Planning",
        "Development Status :: 2 - Pre-Alpha",
#        "Development Status :: 3 - Alpha",
#        "Development Status :: 4 - Beta",
#        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
#        "Intended Audience :: Education",
#        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        'Framework :: Django',
        "Topic :: Database :: Front-Ends",
        "Topic :: Documentation",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
#        "Operating System :: OS Independent",
        "Operating System :: POSIX",
        "Operating System :: Unix",
    ]
)
