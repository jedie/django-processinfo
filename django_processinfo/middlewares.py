"""
    models stuff
    ~~~~~~~~~~~~

    :copyleft: 2011-2018 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


import os
import sys
import time

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import connection
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

from django_processinfo.models import ProcessInfo, SiteStatistics
from django_processinfo.utils.average import average
from django_processinfo.utils.proc_info import process_information


# Save the start time of the current running python instance
overall_start_time = time.monotonic()


def get_processor_times():
    """
    return the accumulated system/user times, in seconds.
    >>> user_time, system_time = get_processor_times()
    """
    user, system, child_user, child_system = os.times()[:4]
    return (user + child_user, system + child_system)


class ProcessInfoMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response

        self.url_filter = []
        for url_name, recusive in settings.PROCESSINFO.URL_FILTER:
            if isinstance(url_name, dict):
                kwargs = url_name
            else:
                kwargs = {"viewname": url_name}
            try:

                url = reverse(**kwargs)
            except Exception:
                etype, evalue, etb = sys.exc_info()
                evalue = etype(f"Wrong django-processinfo URL_FILTER {url_name!r}: {evalue}")
                raise etype(evalue).with_traceback(etb)

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

        # Calculate user/system processor times only for this request:
        user_time, system_time = get_processor_times()
        self.user_time = user_time - self.start_user_time
        self.system_time = system_time - self.start_system_time

        self.response_time = self.own_start_time - self.start_time
        self.overall_time = self.own_start_time - overall_start_time

        process_info, process_created = ProcessInfo.objects.get_or_create(
            pid=self.pid,
            defaults={
                "db_query_count_min": self.query_count,
                "db_query_count_max": self.query_count,
                "db_query_count_avg": self.query_count,
                "response_time_min": self.response_time,
                "response_time_max": self.response_time,
                "response_time_avg": self.response_time,
                "response_time_sum": self.response_time,
                "threads_avg": self.threads,
                "threads_min": self.threads,
                "threads_max": self.threads,
                "user_time_min": self.user_time,
                "user_time_max": self.user_time,
                "user_time_total": self.user_time,
                "system_time_total": self.system_time,
                "system_time_min": self.system_time,
                "system_time_max": self.system_time,
                "vm_peak_min": self.vmpeak,
                "vm_peak_max": self.vmpeak,
                "vm_peak_avg": self.vmpeak,
                "memory_min": self.memory,
                "memory_max": self.memory,
                "memory_avg": self.memory,
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
            process_info.response_time_sum += self.response_time

            process_info.threads_min = min((process_info.threads_min, self.threads))
            process_info.threads_max = max((process_info.threads_max, self.threads))
            process_info.threads_avg = average(
                process_info.threads_avg, self.threads, request_count
            )

            process_info.user_time_min = min((process_info.user_time_min, self.user_time))
            process_info.user_time_max = max((process_info.user_time_min, self.user_time))
            process_info.user_time_total += self.user_time

            process_info.system_time_min = min((process_info.system_time_min, self.system_time))
            process_info.system_time_max = max((process_info.system_time_min, self.system_time))
            process_info.system_time_total += self.system_time

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

            # Auto cleanup ProcessInfo table to protect against overloading.
            queryset = ProcessInfo.objects.order_by('-lastupdate_time')
            max_count = settings.PROCESSINFO.MAX_PROCESSINFO_COUNT
            ids = tuple(queryset[max_count:].values_list('pk', flat=True))
            if ids:
                queryset.filter(pk__in=ids).delete()

    def process_request(self, request):
        """ save start time and database connections count. """
        self.start_time = time.monotonic()

        # We would like to accumulate only the times from processes
        # which are included in statistics. So we not use the absolute
        # processor times.
        self.start_user_time, self.start_system_time = get_processor_times()

        if settings.DEBUG:
            # get number of db queries before we do anything
            self.old_queries = len(connection.queries)

        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        self.own_start_time = time.monotonic()
        self._insert_statistics(exception=True)

    def process_response(self, request, response):

        self.own_start_time = time.monotonic()

        is_200 = response.status_code == 200  # e.g. exclude 304 (HttpResponseNotModified)

        if is_200:
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
                # print "Skip (recusive) %r" % request.path
                return response
            if request.path == url:
                # print "Skip (exact) %r" % request.path
                return response

        self._insert_statistics()

        if is_200 and settings.PROCESSINFO.ADD_INFO and mime_type == "text/html":
            # insert django-processinfo "time cost" info in a html response
            own = time.monotonic() - self.own_start_time
            perc = own / self.response_time * 100
            process_info = settings.PROCESSINFO.INFO_FORMATTER.format(
                own=own * 1000,
                total=self.response_time * 1000,
                perc=perc,
            )
            response.content = response.content.replace(
                settings.PROCESSINFO.INFO_SEARCH_STRING,
                bytes(process_info, encoding="UTF-8")
            )
            response['Content-Length'] = len(response.content)

        return response
