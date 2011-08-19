# coding: utf-8

"""
    django-processinfo - utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyleft: 2011 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


def average(old_avg, current_value, count):
    """
    Calculate the average. Count must start with 0

    >>> average(None, 3.23, 0)
    3.23
    >>> average(0, 1, 0)
    1.0
    >>> average(2.5, 5, 4)
    3.0
    """
    if old_avg is None:
        return current_value
    return (float(old_avg) * count + current_value) / (count + 1)

if __name__ == "__main__":
    import doctest
    print doctest.testmod()
