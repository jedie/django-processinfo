# coding: utf-8

"""
    models stuff
    ~~~~~~~~~~~~

    :copyleft: 2011 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

from __future__ import division, absolute_import
import time
import resource

from django.conf import settings
from django.db import connection

from django_processinfo.models import SiteStatistics, ProcessInfo
from django_processinfo.utils.proc_info import process_information
from django.contrib.sites.models import Site



# Save the start time of the current running python instance
start_overall = time.time()


def average(old_average, current_value, count):
    """
    Calculate the average. Count must start with 0

    >>> average(0, 1, 0)
    1.0
    >>> average(2.5, 5, 4)
    3.0
    """
    return (float(old_average) * count + current_value) / (count + 1)


class ProcessInfoMiddleware(object):
    def process_request(self, request):
        """ save start time and database connections count. """
        self.start_time = time.time()
        if settings.DEBUG:
            # get number of db queries before we do anything
            self.old_queries = len(connection.queries)

    def _update(self, instance):
        instance.request_count += 1
        request_count = instance.request_count

        if settings.DEBUG:
            instance.db_query_count_min = min((instance.db_query_count_min, self.query_count))
            instance.db_query_count_max = max((instance.db_query_count_max, self.query_count))
            instance.db_query_count_average = average(
                instance.db_query_count_average, self.query_count, request_count
            )

        instance.response_time_min = min((instance.response_time_min, self.response_time))
        instance.response_time_max = max((instance.response_time_max, self.response_time))
        instance.response_time_average = average(
            instance.response_time_average, self.response_time, request_count
        )

        instance.threads_min = min((instance.threads_min, self.threads))
        instance.threads_max = max((instance.threads_max, self.threads))
        instance.threads_average = average(
            instance.threads_average, self.threads, request_count
        )

        instance.ru_utime_total += self.ru_utime
        instance.ru_stime_total += self.ru_stime
        instance.ru_utime_min = min((instance.ru_utime_min, self.ru_utime))
        instance.ru_stime_min = min((instance.ru_stime_min, self.ru_stime))
        instance.ru_utime_max = max((instance.ru_utime_min, self.ru_utime))
        instance.ru_stime_max = max((instance.ru_stime_min, self.ru_stime))

        instance.vm_peak_max = max((instance.vm_peak_max, self.vmpeak))

        instance.memory_min = min((instance.memory_min, self.memory))
        instance.memory_max = max((instance.memory_max, self.memory))
        instance.memory_average = average(
            instance.memory_average, self.memory, request_count
        )

    def process_response(self, request, response):
        """ calculate the statistic """
        own_start_time = time.time()

        if settings.DEBUG:
            self.query_count = len(connection.queries) - self.old_queries
        else:
            self.query_count = 0

        p = dict(process_information())
        self.pid = p["Pid"]
        self.threads = p["Threads"]
        self.vmpeak = p["VmPeak"]
        self.memory = p["VmRSS"]

        self_rusage = resource.getrusage(resource.RUSAGE_SELF)
        self.ru_stime = self_rusage.ru_stime
        self.ru_utime = self_rusage.ru_utime

        self.response_time = own_start_time - self.start_time
        self.overall_time = own_start_time - start_overall

        defaults = {
            "db_query_count_min":self.query_count,
            "db_query_count_max":self.query_count,
            "db_query_count_average":self.query_count,
            "request_count":1,
            "response_time_min":self.response_time,
            "response_time_max":self.response_time,
            "response_time_average":self.response_time,
            "threads_average": self.threads,
            "threads_min":self.threads,
            "threads_max":self.threads,
            "ru_utime_total":self.ru_utime,
            "ru_stime_total":self.ru_stime,
            "ru_utime_min":self.ru_utime,
            "ru_stime_min":self.ru_stime,
            "ru_utime_max":self.ru_utime,
            "ru_stime_max":self.ru_stime,
            "vm_peak_max":self.vmpeak,
            "memory_min":self.memory,
            "memory_max":self.memory,
            "memory_average":self.memory,
        }

        site_stats_defaults = defaults.copy()
        site_stats_defaults.update({
            "total_processes":1,
            "process_count_average":1,
            "process_count_max":1,
        })

        site_stats, created = SiteStatistics.objects.get_or_create(
            site=Site.objects.get_current(),
            defaults=site_stats_defaults
        )
        if not created:
            self._update(site_stats)
            site_stats.save()

        process_info, created = ProcessInfo.objects.get_or_create(
            pid=self.pid,
            defaults=defaults
        )
        if not created:
            self._update(process_info)
            process_info.save()

        if settings.PROCESSINFO.ADD_INFO and "html" in response._headers["content-type"][1]:
            # insert django-processinfo "time cost" info in a html response
            response.content = response.content.replace(
                settings.PROCESSINFO.INFO_SEARCH_STRING,
                settings.PROCESSINFO.INFO_FORMATTER % round((time.time() - own_start_time) * 1000, 1)
            )

        return response

if __name__ == "__main__":
    import doctest
    print doctest.testmod()
