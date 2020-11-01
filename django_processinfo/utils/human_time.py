"""
    django-processinfo - utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyleft: 2011-2018 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import datetime

from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from pytz.reference import LocalTimezone


def datetime2float(t):
    """
    >>> datetime2float(datetime.timedelta(seconds=1))
    1.0

    >>> f = datetime2float(datetime.timedelta(weeks=2, seconds=20.1, microseconds=100))
    >>> f
    1209620.1001
    >>> f == 20.1 + 0.0001 + 2 * 7 * 24 * 60 * 60
    True

    >>> datetime2float("type error")
    Traceback (most recent call last):
        ...
    TypeError: datetime2float() argument must be a timedelta instance.
    """
    if not isinstance(t, datetime.timedelta):
        raise TypeError("datetime2float() argument must be a timedelta instance.")

    # timedelta.total_seconds() is new in Python 2.7
    return (float(t.microseconds) + (t.seconds + t.days * 24 * 3600) * 1E6) / 1E6


def timesince2(d, now=None):
    """
    Simmilar to django.utils.timesince.timesince, but:
        * display "X Sec" and "X ms", too
        * generates html code with both information

    >>> timesince2(datetime.datetime(2005, 7, 14, 0), datetime.datetime(2005, 7, 16, 12))
    u'<span title="July 14, 2005, midnight" style="cursor:help;">2.5 days</span>'

    >>> timesince2(datetime.datetime(2005, 7, 14, 12, 30, 00), datetime.datetime(2005, 7, 14, 12, 30, 10))
    u'<span title="July 14, 2005, 12:30 p.m." style="cursor:help;">10.0 sec</span>'

    >>> timesince2(datetime.datetime(2005, 7, 14, 12, 30, 00), datetime.datetime(2005, 7, 14, 12, 30, 00, 1200))
    u'<span title="July 14, 2005, 12:30 p.m." style="cursor:help;">1.2 ms</span>'
    """
    if not isinstance(d, datetime.datetime):
        # Convert datetime.date to datetime.datetime for comparison.
        d = datetime.datetime(d.year, d.month, d.day)

    if now is None:
        if d.tzinfo:
            now = datetime.datetime.now(LocalTimezone(d))
        else:
            now = datetime.datetime.now()
    elif not isinstance(now, datetime.datetime):
        # Convert datetime.date to datetime.datetime
        now = datetime.datetime(now.year, now.month, now.day)

    # ignore microsecond part of 'd' since we removed it from 'now'
    delta = now - (d - datetime.timedelta(0, 0, d.microsecond))

    result = human_duration(delta)

    context = {"d": d, "timesince": result}
    return render_to_string("django_processinfo/timesince.html", context)


def human_duration(t):
    """
    Converts a time duration into a friendly text representation.

    >>> human_duration("type error")
    Traceback (most recent call last):
        ...
    TypeError: human_duration() argument must be timedelta, integer or float)

    >>> human_duration(None)
    u'None'
    >>> human_duration(datetime.timedelta(microseconds=1000))
    u'1.0 ms'
    >>> human_duration(0.01)
    u'10.0 ms'
    >>> human_duration(0.9)
    u'900.0 ms'
    >>> human_duration(datetime.timedelta(seconds=1))
    u'1.0 sec'
    >>> human_duration(65.5)
    u'1.1 min'
    >>> human_duration((60 * 60)-1)
    u'59.0 min'
    >>> human_duration(60*60)
    u'1.0 hours'
    >>> human_duration(1.05*60*60)
    u'1.1 hours'
    >>> human_duration(datetime.timedelta(hours=24))
    u'1.0 days'
    >>> human_duration(2.54 * 60 * 60 * 24 * 365)
    u'2.5 years'
    """
    if t is None:
        return "None"
    elif isinstance(t, datetime.timedelta):
        # timedelta.total_seconds() is new in Python 2.7
        t = datetime2float(t)
    elif not isinstance(t, (int, float)):
        raise TypeError("human_duration() argument must be timedelta, integer or float)")

    chunks = (
        (60 * 60 * 24 * 365, _('years')),
        (60 * 60 * 24 * 30, _('months')),
        (60 * 60 * 24 * 7, _('weeks')),
        (60 * 60 * 24, _('days')),
        (60 * 60, _('hours')),
    )

    if t < 1:
        return _("%.1f ms") % round(t * 1000, 1)
    if t < 60:
        return _("%.1f sec") % round(t, 1)
    if t < 60 * 60:
        return _("%.1f min") % round(t / 60, 1)

    for seconds, name in chunks:
        count = t / seconds
        if count >= 1:
            count = round(count, 1)
            break
    return f"{count:.1f} {name}"
