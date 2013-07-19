# coding: utf-8

"""
    version info
    ~~~~~~~~~~~~

    :copyleft: 2011-2013 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


__version__ = (0, 7, 0, "dev")


VERSION_STRING = '.'.join(str(part) for part in __version__)


if __name__ == "__main__":
    print VERSION_STRING
