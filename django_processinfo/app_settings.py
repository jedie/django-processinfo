"""
    django-processinfo app settings
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    All own settings for the django-processinfo app.

    **IMPORTANT:**
        You should not edit this file!

    Add this into your settings.py:

        from django_processinfo import app_settings as PROCESSINFO
        PROCESSINFO.ADD_INFO = True # e.g. to change a settings


    :copyleft: 2011-2012 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import sys


# Used by a few dynamic settings:
RUN_WITH_DEV_SERVER = "runserver" in sys.argv

# Delete oldest ProcessInfo entries if max count exists:
MAX_PROCESSINFO_COUNT = 100

# Should the django-processinfo "time cost" info inserted in a html page?
ADD_INFO = True

# Substring for replace with INFO_FORMATTER
INFO_SEARCH_STRING = b"</body>"
INFO_FORMATTER = (
    '<p class="django-processinfo">'
    '<small>'
    'django-processinfo: {own:.1f} ms of {total:.1f} ms ({perc:.1f}%)'
    '</small>'
    '</p>'
    '</body>'
)


# ONLY_MIME_TYPES == None or tuple
# To specify what response should be include in statistics.
# Set ONLY_MIME_TYPES = None for all mime types
if RUN_WITH_DEV_SERVER:
    # Capture only this mime types:
    ONLY_MIME_TYPES = ("text/html",)
else:
    # Capture all mime types
    ONLY_MIME_TYPES = None


# URL_FILTER to exclude urls/views from statistic:
URL_FILTER = (
    # Syntax: (URL name as String or parameters as dict, Bool: recusive or not)

    # To exclude all django admin panel views, use this:
    # ("admin:index", True),

    # Exclude only explicit one url, e.g.:
    # ("/foo/bar/", False),

    # You can also pass parameters to urlresolvers.reverse():
    # Exclude the views and "subviews" of Django-processinfo models in django admin:
    # ({"viewname": "admin:app_list", "args": ("django_processinfo",)}, True),
)
