# coding: utf-8

"""
    django-processinfo - utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyleft: 2011 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import datetime

from django.utils.tzinfo import LocalTimezone
from django.utils.timesince import timesince


def timesince2(d, now=None):
    """
    Same as django.utils.timesince.timesince but display "X Sec" and "X ms", too.
    """
    result = timesince(d, now)
    if result.startswith("0 "):
        if now is None:
            if d.tzinfo:
                now = datetime.datetime.now(LocalTimezone(d))
            else:
                now = datetime.datetime.now()

        diff = now - d

        # timedelta.total_seconds() is new in Python 2.7
        diff_float = (diff.microseconds / 1E6) + diff.seconds

        if diff.seconds == 0:
            result = u"%.f ms" % (diff_float * 1000)
        else:
            result = u"%.2f Sec" % diff_float

    return result
