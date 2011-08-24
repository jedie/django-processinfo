# coding: utf-8

"""
    models stuff
    ~~~~~~~~~~~~

    :copyleft: 2011 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

from __future__ import division, absolute_import

import os
import time

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db.models.aggregates import Avg, Sum
from django.http import HttpResponseRedirect
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext as _

from django_processinfo.models import SiteStatistics, ProcessInfo
from django_processinfo.utils.average import average
from django_processinfo import VERSION_STRING
from django_processinfo.utils.proc_info import meminfo
from django_processinfo.utils.human_time import timesince2, human_duration, \
    datetime2float


class BaseModelAdmin(admin.ModelAdmin):
    def start_time2(self, obj):
        return timesince2(obj.start_time)
    start_time2.short_description = _("start since")
    start_time2.admin_order_field = "start_time"
    start_time2.allow_tags = True

    def changelist_view(self, request, extra_context=None):
        self.request = request # work-a-round for https://code.djangoproject.com/ticket/13659

        site_count = 0
        first_start_time = None

        process_count_max = 0
        process_spawn = 0
        process_count_avg = 0.0

        life_time_values = []
        request_count = 0
        exception_count = 0

        memory_min_avg = 0.0
        memory_avg = 0.0
        memory_max_avg = 0.0

        vm_peak_min_avg = 0.0
        vm_peak_max_avg = 0.0
        vm_peak_avg = 0.0

        threads_min_avg = None
        threads_max_avg = None
        threads_avg = None

        response_time_min_avg = None
        response_time_max_avg = None
        response_time_avg = None

        self.aggregate_data = {}
        queryset = SiteStatistics.objects.all()
        for site_stats in queryset:
            site_count += 1

            if first_start_time is None or site_stats.start_time < first_start_time:
                first_start_time = site_stats.start_time

            site_stats.update_informations()
            site_stats.save()

            process_count_max += site_stats.process_count_max
            process_spawn += site_stats.process_spawn
            process_count_avg += site_stats.process_count_avg

            site = site_stats.site

            processes = ProcessInfo.objects.filter(site=site).only("start_time", "lastupdate_time")
            for process in processes:
                life_time = process.lastupdate_time - process.start_time
                life_time_values.append(life_time)

            data = ProcessInfo.objects.filter(site=site).aggregate(
                # VmRSS
                Avg("memory_min"),
                Avg("memory_avg"),
                Avg("memory_max"),

                # VmPeak
                Avg("vm_peak_min"),
                Avg("vm_peak_avg"),
                Avg("vm_peak_max"),

                Sum("request_count"),
                Sum("exception_count"),

                Avg("threads_min"),
                Avg("threads_avg"),
                Avg("threads_max"),

                Avg("response_time_min"),
                Avg("response_time_avg"),
                Avg("response_time_max"),
            )
            self.aggregate_data[site] = data

            request_count += data["request_count__sum"] or 1
            exception_count += data["exception_count__sum"] or 0

            # VmRSS
            memory_min_avg += (data["memory_min__avg"]or 0) * process_count_avg
            memory_avg += (data["memory_avg__avg"] or 0) * process_count_avg
            memory_max_avg += (data["memory_max__avg"] or 0) * process_count_avg

            # VmPeak
            vm_peak_min_avg += (data["vm_peak_min__avg"] or 0) * process_count_avg
            vm_peak_avg += (data["vm_peak_avg__avg"] or 0) * process_count_avg
            vm_peak_max_avg += (data["vm_peak_max__avg"] or 0) * process_count_avg

            threads_min_avg = average(
                threads_min_avg, data["threads_min__avg"] or 1, site_count
            )
            threads_avg = average(
                threads_avg, data["threads_avg__avg"] or 1, site_count
            )
            threads_max_avg = average(
                threads_max_avg, data["threads_max__avg"] or 1, site_count
            )

            response_time_min_avg = average(
                response_time_min_avg, data["response_time_min__avg"] or 0, site_count
            )
            response_time_avg = average(
                response_time_avg, data["response_time_avg__avg"] or 0, site_count
            )
            response_time_max_avg = average(
                response_time_max_avg, data["response_time_max__avg"] or 0, site_count
            )

        # Calculate the process life times
        # timedelta.total_seconds() is new in Python 2.7
        life_time_values = [datetime2float(td) for td in life_time_values]
        life_time_min = min(life_time_values)
        life_time_max = max(life_time_values)
        life_time_avg = sum(life_time_values) / len(life_time_values)

        # get information from /proc/meminfo    
        meminfo_dict = dict(meminfo())
        swap_used = meminfo_dict["SwapTotal"] - meminfo_dict["SwapFree"]
        mem_free = meminfo_dict["MemFree"] + meminfo_dict["Buffers"] + meminfo_dict["Cached"]
        mem_used = meminfo_dict["MemTotal"] - mem_free

        extra_context = {
            "site_count":site_count,

            "first_start_time": first_start_time,

            "process_spawn":process_spawn,
            "process_count_max":process_count_max,
            "process_count_avg": process_count_avg,

            "request_count": request_count,
            "exception_count": exception_count,

            "memory_min_avg":memory_min_avg,
            "memory_max_avg":memory_max_avg,
            "memory_avg":memory_avg,

            "vm_peak_min_avg": vm_peak_min_avg,
            "vm_peak_max_avg": vm_peak_max_avg,
            "vm_peak_avg": vm_peak_avg,

            "threads_min_avg": threads_min_avg,
            "threads_max_avg": threads_max_avg,
            "threads_avg": threads_avg,

            "response_time_min_avg": u"%.1fms" % (response_time_min_avg * 1000),
            "response_time_max_avg": u"%.1fms" % (response_time_max_avg * 1000),
            "response_time_avg": u"%.1fms" % (response_time_avg * 1000),

            "version_string": VERSION_STRING,

            "life_time_min": human_duration(life_time_min),
            "life_time_max": human_duration(life_time_max),
            "life_time_avg": human_duration(life_time_avg),

            "mem_used": mem_used,
            "mem_perc": float(mem_used) / meminfo_dict["MemTotal"] * 100,
            "mem_total": meminfo_dict["MemTotal"],

            "swap_used": swap_used,
            "swap_perc": float(swap_used) / meminfo_dict["SwapTotal"] * 100,
            "swap_total": meminfo_dict["SwapTotal"],
        }

        try:
            extra_context["loadavg"] = os.getloadavg()
        except OSError, err:
            extra_context["loadavg_err"] = "[Error: %s]" % err

        return super(BaseModelAdmin, self).changelist_view(request, extra_context=extra_context)


class SiteStatisticsAdmin(BaseModelAdmin):
    def sum_memory_avg(self, obj):
        """
        The memory average (VmRSS) for all processes for this site
        """
        aggregate_data = self.aggregate_data[obj.site]
        memory_avg = aggregate_data["memory_avg__avg"] or 0
        memory_sum_avg = memory_avg * obj.process_count_avg
        return filesizeformat(memory_sum_avg)
    sum_memory_avg.short_description = _("Avg VmRSS")

    def sum_vm_peak(self, obj):
        aggregate_data = self.aggregate_data[obj.site]
        vm_peak_avg = aggregate_data["vm_peak_avg__avg"] or 0
        sum_vm_peak = vm_peak_avg * obj.process_count_avg
        return filesizeformat(sum_vm_peak)
    sum_vm_peak.short_description = _("Avg VmPeak")

    def response_time_avg(self, obj):
        aggregate_data = self.aggregate_data[obj.site]
        response_time_avg = aggregate_data["response_time_avg__avg"] or 0
        return u"%.1fms" % (response_time_avg * 1000)
    response_time_avg.short_description = _("Avg response time")

    def request_count(self, obj):
        aggregate_data = self.aggregate_data[obj.site]
        return aggregate_data["request_count__sum"] or 1
    request_count.short_description = _("Requests")

    def exception_count(self, obj):
        aggregate_data = self.aggregate_data[obj.site]
        return aggregate_data["exception_count__sum"] or 0
    exception_count.short_description = _("Exceptions")

    def process_count_avg2(self, obj):
        return u"%.1f" % round(obj.process_count_avg, 1)
    process_count_avg2.short_description = _("Avg process count")
    process_count_avg2.admin_order_field = "process_count_avg"

    list_display = [
        "site",
        "sum_memory_avg", "sum_vm_peak",
        "response_time_avg", "request_count", "exception_count",
        "process_spawn", "process_count_avg2", "process_count_max",
        "start_time2",
    ]
#    if not settings.DEBUG:
#        del(list_display[list_display.index("db_query_count_avg")])

admin.site.register(SiteStatistics, SiteStatisticsAdmin)


class ProcessInfoAdmin(BaseModelAdmin):
    def lastupdate_time2(self, obj):
        return timesince2(obj.lastupdate_time)
    lastupdate_time2.short_description = _("last update")
    lastupdate_time2.admin_order_field = "lastupdate_time"
    lastupdate_time2.allow_tags = True

    def life_time(self, obj):
        return timesince2(obj.start_time, obj.lastupdate_time)
    life_time.short_description = _("life time")
    life_time.allow_tags = True

    def response_time_avg2(self, obj):
        return u"%.1fms" % (obj.response_time_avg * 1000)
    response_time_avg2.short_description = _("Avg response time")
    response_time_avg2.admin_order_field = "response_time_avg"

    def memory_avg2(self, obj):
        return filesizeformat(obj.memory_avg)
    memory_avg2.short_description = _("Avg VmRSS")
    memory_avg2.admin_order_field = "memory_avg"

    def vm_peak_avg2(self, obj):
        return filesizeformat(obj.vm_peak_avg)
    vm_peak_avg2.short_description = _("VmPeak")
    vm_peak_avg2.admin_order_field = "vm_peak_avg"

    def alive2(self, obj):
        """ Check if current process is active and mark it if it's dead. """
        active = os.path.exists("/proc/%i/status" % obj.pid)
        if not active and obj.alive != False:
            obj.alive = False
            obj.save()
            if settings.DEBUG:
                self.message_user(self.request, _("Mark process with pid %r as dead.") % obj.pid)
        return active
    alive2.boolean = True
    alive2.short_description = _("alive")
    alive2.admin_order_field = "alive"

    def remove_dead_entries(self, request, queryset):
        """
        TODO: Create a link in "object tools" in changelist template
        """
        start_time = time.time()
        # Check that the user has delete permission for the actual model
        if not self.has_delete_permission(request):
            raise PermissionDenied

        queryset = self.model.objects.all().only("pid")
        ids_to_delete = []
        for instance in queryset:
            if not self.active(instance):
                ids_to_delete.append(instance.pk)

        queryset = self.model.objects.filter(pk__in=ids_to_delete)
        queryset.delete()

        self.message_user(request, _("Successfully deleted %(count)d dead entries in %(time).1fms.") % {
            "count": len(ids_to_delete), "time": ((time.time() - start_time) * 1000)
        })
        return HttpResponseRedirect(request.path)
    remove_dead_entries.short_description = _("Remove all dead processes")

    list_display = [
        "pid", "alive2", "site", "request_count", "exception_count", "db_query_count_avg",
        "response_time_avg2",
        "memory_avg2", "vm_peak_avg2",
        "start_time2", "lastupdate_time2", "life_time"
    ]
    if not settings.DEBUG:
        del(list_display[list_display.index("db_query_count_avg")])
    actions = [remove_dead_entries]

admin.site.register(ProcessInfo, ProcessInfoAdmin)
