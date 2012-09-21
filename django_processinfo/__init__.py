# coding: utf-8

"""
    version info
    ~~~~~~~~~~~~

    :copyleft: 2011-2012 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


__version__ = (0, 6, 4)


VERSION_STRING = '.'.join(str(part) for part in __version__)


if __name__ == "__main__":
    print VERSION_STRING
