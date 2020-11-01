"""
    django-processinfo - utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    http://kernel.org/doc/Documentation/filesystems/proc.txt

    :copyleft: 2011 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


import datetime


def process_information(pid=None):
    """
    Get process information.

    If pid == None: We use "self" to get the current process information.

    Note:
      * Will only work if /proc/$$/status exists (where $$ is the given pid).
      * We don't catch the error, if /proc/$$/status doesn't exists!
      * All values convert to integers (kB values convertet to bytes)

    returns a tuple, which can be easy convert info a dict, e.g.:

    try:
        p = dict(process_information())
    except IOError, err:
        print "Error: %s" % err
    else:
        print "Peak virtual memory size: %i Bytes" % p["VmPeak"]

    see also: http://www.python-forum.de/viewtopic.php?f=11&t=27178 (de)
    """
    if pid is None:
        pid = "self"
    path = f"/proc/{pid}/status"

    result = []
    with open(path) as f:
        for line in f:
            key, values = [i.strip() for i in line.split(":", 1)]
            if "\t" in values:
                values2 = values.split("\t")
            else:
                values2 = values.split(" ")

            length = len(values2)
            if length == 1:
                if len(values) == 16:
                    result.append((key, values))
                else:
                    try:
                        result.append((key, int(values)))
                    except ValueError:
                        result.append((key, values))
                continue
            elif length == 2:
                if values2[1].lower() == "kb":
                    result.append((key, int(values2[0]) * 1024))
                    continue

            try:
                result.append((key, [int(v) for v in values2]))
            except ValueError:
                result.append((key, values))

    return tuple(result)


def meminfo():
    """
    returns information from /proc/meminfo

    Note:
      * Will only work if /proc/meminfo exists
      * We don't catch the error, if /proc/meminfo doesn't exists!
      * All values convert to integers (kB values convertet to bytes)

    returns a tuple, which can be easy convert info a dict, e.g.:

    try:
        m = dict(meminfo())
    except IOError, err:
        print "Error: %s" % err
    else:
        print "free: %i Bytes" % m["MemFree"]
    """

    result = []
    with open("/proc/meminfo") as f:
        for line in f:
            key, values = [i.strip() for i in line.split(":", 1)]
            values2 = values.split(" ")
            length = len(values2)
            if length == 1:
                try:
                    result.append((key, int(values)))
                except ValueError:
                    result.append((key, values))
                continue
            elif length == 2:
                if values2[1].lower() == "kb":
                    result.append((key, int(values2[0]) * 1024))
                    continue
            try:
                result.append((key, [int(v) for v in values2]))
            except ValueError:
                result.append((key, values))

    return tuple(result)


def uptime_infomation():
    """
    Returns a dict with informations from /proc/uptime
    """
    with open("/proc/uptime") as f:
        raw_uptime = f.readline().strip().split(" ")[0]
        uptime_sec = float(raw_uptime)

    d = datetime.datetime.now() - datetime.timedelta(seconds=uptime_sec)
    return d


if __name__ == "__main__":
    p = process_information()
    import pprint
    pprint.pprint(p)

    try:
        p = dict(process_information())
    except OSError as err:
        print(f"Error: {err}")
    else:
        print("Peak virtual memory size: %i Bytes" % p["VmPeak"])

    m = meminfo()
    pprint.pprint(m)
    try:
        m = dict(meminfo())
    except OSError as err:
        print(f"Error: {err}")
    else:
        print("free: %i Bytes" % m["MemFree"])

    print("uptime_infomation():", uptime_infomation())
