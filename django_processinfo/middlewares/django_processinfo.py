# coding: utf-8

"""
    models stuff
    ~~~~~~~~~~~~

    :copyleft: 2011 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

from __future__ import division, absolute_import
import resource
import sys
import time

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.db import connection

from django_processinfo.models import SiteStatistics, ProcessInfo
from django_processinfo.utils.average import average
from django_processinfo.utils.proc_info import process_information


# Save the start time of the current running python instance
overall_start_time = time.time()


class ProcessInfoMiddleware(object):
    def __init__(self):
        self.url_filter = []
        for url_name, recusive in settings.PROCESSINFO.URL_FILTER:
            if isinstance(url_name, dict):
                kwargs = url_name
            else:
                kwargs = {"viewname":url_name}
            try:

                url = urlresolvers.reverse(**kwargs)
            except Exception:
                etype, evalue, etb = sys.exc_info()
                evalue = etype("Wrong django-processinfo URL_FILTER %r: %s" % (url_name, evalue))
                raise etype, evalue, etb

            self.url_filter.append((url, recusive))
        self.url_filter = tuple(self.url_filter)

    def _insert_statistics(self, exception=False):
        """ collect statistic information """

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

        self.response_time = self.own_start_time - self.start_time
        self.overall_time = self.own_start_time - overall_start_time

        process_info, process_created = ProcessInfo.objects.get_or_create(
            pid=self.pid,
            defaults={
                "db_query_count_min":self.query_count,
                "db_query_count_max":self.query_count,
                "db_query_count_avg":self.query_count,
                "response_time_min":self.response_time,
                "response_time_max":self.response_time,
                "response_time_avg":self.response_time,
                "threads_avg": self.threads,
                "threads_min":self.threads,
                "threads_max":self.threads,
                "ru_utime_total":self.ru_utime,
                "ru_stime_total":self.ru_stime,
                "ru_utime_min":self.ru_utime,
                "ru_stime_min":self.ru_stime,
                "ru_utime_max":self.ru_utime,
                "ru_stime_max":self.ru_stime,
                "vm_peak_min":self.vmpeak,
                "vm_peak_max":self.vmpeak,
                "vm_peak_avg":self.vmpeak,
                "memory_min":self.memory,
                "memory_max":self.memory,
                "memory_avg":self.memory,
            }
        )
        if exception:
            process_info.exception_count += 1

        if not process_created:
            process_info.request_count += 1
            request_count = process_info.request_count

            if settings.DEBUG:
                process_info.db_query_count_min = min((process_info.db_query_count_min, self.query_count))
                process_info.db_query_count_max = max((process_info.db_query_count_max, self.query_count))
                process_info.db_query_count_avg = average(
                    process_info.db_query_count_avg, self.query_count, request_count
                )

            process_info.response_time_min = min((process_info.response_time_min, self.response_time))
            process_info.response_time_max = max((process_info.response_time_max, self.response_time))
            process_info.response_time_avg = average(
                process_info.response_time_avg, self.response_time, request_count
            )

            process_info.threads_min = min((process_info.threads_min, self.threads))
            process_info.threads_max = max((process_info.threads_max, self.threads))
            process_info.threads_avg = average(
                process_info.threads_avg, self.threads, request_count
            )

            process_info.ru_utime_total += self.ru_utime
            process_info.ru_stime_total += self.ru_stime
            process_info.ru_utime_min = min((process_info.ru_utime_min, self.ru_utime))
            process_info.ru_stime_min = min((process_info.ru_stime_min, self.ru_stime))
            process_info.ru_utime_max = max((process_info.ru_utime_min, self.ru_utime))
            process_info.ru_stime_max = max((process_info.ru_stime_min, self.ru_stime))

            process_info.vm_peak_min = min((process_info.vm_peak_min, self.vmpeak))
            process_info.vm_peak_max = max((process_info.vm_peak_max, self.vmpeak))
            process_info.vm_peak_avg = average(
                process_info.vm_peak_avg, self.vmpeak, request_count
            )

            process_info.memory_min = min((process_info.memory_min, self.memory))
            process_info.memory_max = max((process_info.memory_max, self.memory))
            process_info.memory_avg = average(
                process_info.memory_avg, self.memory, request_count
            )
            process_info.save()


        current_site = Site.objects.get_current()
        site_stats, created = SiteStatistics.objects.get_or_create(
            site=current_site
        )
        if created or process_created:
            if not created and process_created:
                site_stats.process_spawn += 1
            site_stats.update_informations()
            site_stats.save()


    def process_request(self, request):
        """ save start time and database connections count. """
        self.start_time = time.time()
        if settings.DEBUG:
            # get number of db queries before we do anything
            self.old_queries = len(connection.queries)


    def process_exception(self, request, exception):
        self.own_start_time = time.time()
        self._insert_statistics(exception=True)


    def process_response(self, request, response):

        self.own_start_time = time.time()

        mime_type = response["content-type"].split(";", 1)[0]

        # Exclude this response by mime type
        if settings.PROCESSINFO.ONLY_MIME_TYPES is not None:
            # Capture only specific mime types 
            if mime_type not in settings.PROCESSINFO.ONLY_MIME_TYPES:
                # Don't capture this mime type
                return response

        # Exclude this response by settings.PROCESSINFO.URL_FILTER
        for url, recusive in self.url_filter:
            if recusive and request.path.startswith(url):
                #print "Skip (recusive) %r" % request.path
                return response
            if request.path == url:
                #print "Skip (exact) %r" % request.path
                return response

        self._insert_statistics()

        if settings.PROCESSINFO.ADD_INFO and mime_type == "text/html":
            # insert django-processinfo "time cost" info in a html response
            own = time.time() - self.own_start_time
            perc = own / self.response_time * 100
            response.content = response.content.replace(
                settings.PROCESSINFO.INFO_SEARCH_STRING,
                settings.PROCESSINFO.INFO_FORMATTER % {
                    "own":own * 1000,
                    "total":self.response_time * 1000,
                    "perc":perc,
                }
            )

        return response
