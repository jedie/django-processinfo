# coding: utf-8

"""
    models stuff
    ~~~~~~~~~~~~

    :copyleft: 2011 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

from __future__ import division, absolute_import
import time

from django.conf import settings
from django.db import connection

from django_processinfo.models import SiteStatistics, ProcessInfo
from django_processinfo.utils.proc_info import process_information
from django.contrib.sites.models import Site


# Save the start time of the current running python instance
start_overall = time.time()


class ProcessInfoMiddleware(object):
    def process_request(self, request):
        """ save start time and database connections count. """
        self.start_time = time.time()
        if settings.DEBUG:
            # get number of db queries before we do anything
            self.old_queries = len(connection.queries)

    def process_response(self, request, response):
        """ calculate the statistic """

        if settings.DEBUG:
            own_start_time = time.time()
            query_count = len(connection.queries) - self.old_queries
        else:
            query_count = 0

        total_time = own_start_time - self.start_time
        overall_time = own_start_time - start_overall

        p = dict(process_information())
        pid = p["Pid"]

        # TODO:
        site_stats = SiteStatistics.objects.get_or_create(
            site=Site.objects.get_current(),
            defaults={}
        )
        ProcessInfo.objects.get_or_create(
            pid=pid,
            defaults={}
        )

        if settings.DEBUG and "html" in response._headers["content-type"][1]:
            response = response.replace("</body>",
                "<p>django-processinfo: %.1f ms</p>" % round((time.time() - own_start_time) * 1000, 1)
            )

        return response
