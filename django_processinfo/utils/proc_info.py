# coding: utf-8

"""
    models stuff
    ~~~~~~~~~~~~

    :copyleft: 2011 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


def process_information(pid=None):
    """
    Get process information.

    If pid == None: We use "self" to get the current process information.

    Note:
      * Will only work if /proc/$$/status exists (where $$ is the given pid).
      * We don't cache the error, if /proc/$$/status doesn't exists!
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
    path = "/proc/%s/status" % pid

    result = []
    with open(path, "r") as f:
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
                    except ValueError, err:
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

if __name__ == "__main__":
    import pprint
    p = process_information()
    pprint.pprint(p)
