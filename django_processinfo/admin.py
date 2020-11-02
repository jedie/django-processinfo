"""
    models stuff
    ~~~~~~~~~~~~

    :copyleft: 2011-2018 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


import os
import socket
import sys
import time

from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.db.models.aggregates import Avg, Max, Min, Sum
from django.http import HttpResponseRedirect
from django.template.defaultfilters import filesizeformat
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from django_processinfo import __version__
from django_processinfo.models import ProcessInfo, SiteStatistics
from django_processinfo.utils.average import average
from django_processinfo.utils.human_time import datetime2float, human_duration, timesince2
from django_processinfo.utils.proc_info import meminfo, process_information, uptime_infomation


# Collect some static informations
try:
    domain_name = socket.getfqdn()
except Exception as err:
    domain_name = f"[Error: {err}]"
    ip_addresses = "-"
else:
    try:
        ip_addresses = ", ".join(socket.gethostbyname_ex(domain_name)[2])
    except Exception as err:
        ip_addresses = f"[Error: {err}]"

STATIC_INFORMATIONS = {
    "python_version": f"{sys.version}",
    "sys_prefix": sys.prefix,
    "os_uname": " ".join(os.uname()),

    "domain_name": domain_name,
    "ip_addresses": ip_addresses,
}


class BaseModelAdmin(admin.ModelAdmin):
    def start_time2(self, obj):
        return timesince2(obj.start_time)
    start_time2.short_description = _("start since")
    start_time2.admin_order_field = "start_time"
    start_time2.allow_tags = True

    def changelist_view(self, request, extra_context=None):
        self.request = request  # work-a-round for https://code.djangoproject.com/ticket/13659

        site_count = 0
        first_start_time = None

        process_count_current = 0
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

        threads_current = 0
        threads_min = 99999
        threads_max = 0
        threads_avg = None

        response_time_min_avg = None
        response_time_max_avg = None
        response_time_avg = None
        response_time_sum = 0.0

        user_time_total = 0.0  # total user mode time
        system_time_total = 0.0  # total system mode time

        self.aggregate_data = {}
        queryset = SiteStatistics.objects.all()
        for site_stats in queryset:
            site_count += 1

            if first_start_time is None or site_stats.start_time < first_start_time:
                first_start_time = site_stats.start_time

            living_pids = site_stats.update_informations()
            site_stats.save()

            for pid in living_pids:
                try:
                    p = dict(process_information(pid))
                except OSError:  # Process dead -> mark as dead
                    process = ProcessInfo.objects.get(pid=pid)
                    process.alive = False
                    process.save()
                    continue
                threads_current += p["Threads"]

            living_process_count = len(living_pids)
            process_count_current += living_process_count
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

                Min("threads_min"),
                Avg("threads_avg"),
                Max("threads_max"),

                Avg("response_time_min"),
                Avg("response_time_avg"),
                Avg("response_time_max"),
                Sum("response_time_sum"),

                Sum("user_time_total"),  # total user mode time
                Sum("system_time_total"),  # total system mode time
            )
            data["living_process_count"] = living_process_count
            self.aggregate_data[site] = data

            request_count += data["request_count__sum"] or 1
            exception_count += data["exception_count__sum"] or 0

            # VmRSS
            memory_min_avg += (data["memory_min__avg"] or 0) * process_count_avg
            memory_avg += (data["memory_avg__avg"] or 0) * process_count_avg
            memory_max_avg += (data["memory_max__avg"] or 0) * process_count_avg

            # VmPeak
            vm_peak_min_avg += (data["vm_peak_min__avg"] or 0) * process_count_avg
            vm_peak_avg += (data["vm_peak_avg__avg"] or 0) * process_count_avg
            vm_peak_max_avg += (data["vm_peak_max__avg"] or 0) * process_count_avg

            threads_min = min([threads_min, data["threads_min__min"] or 9999])
            threads_max = max([threads_max, data["threads_max__max"] or 1])
            threads_avg = average(
                threads_avg, data["threads_avg__avg"] or 1, site_count
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
            response_time_sum += data["response_time_sum__sum"] or 0

            user_time_total += data["user_time_total__sum"] or 0  # total user mode time
            system_time_total += data["system_time_total__sum"] or 0  # total system mode time

        # Calculate the process life times
        # timedelta.total_seconds() is new in Python 2.7
        if not life_time_values:  # First request with empty data
            life_time_min = 0
            life_time_max = 0
            life_time_avg = 0
        else:
            life_time_values = [datetime2float(td) for td in life_time_values]
            life_time_min = min(life_time_values)
            life_time_max = max(life_time_values)
            life_time_avg = sum(life_time_values) / len(life_time_values)

        # get information from /proc/meminfo
        meminfo_dict = dict(meminfo())
        swap_used = meminfo_dict["SwapTotal"] - meminfo_dict["SwapFree"]
        mem_free = meminfo_dict["MemFree"] + meminfo_dict["Buffers"] + meminfo_dict["Cached"]
        mem_used = meminfo_dict["MemTotal"] - mem_free

        # information from /proc/uptime
        updatetime = uptime_infomation()

        swap_total = meminfo_dict["SwapTotal"]
        if swap_total > 0:
            swap_perc = float(swap_used) / swap_total * 100
        else:
            # e.g. no SWAP used
            swap_perc = 0

        try:
            loads = (user_time_total + system_time_total) / response_time_sum * 100
        except Exception as err:
            loads = f"ERROR: {err}"

        extra_context = {
            "site_count": site_count,

            "first_start_time": first_start_time,

            "process_count_current": process_count_current,
            "process_spawn": process_spawn,
            "process_count_max": process_count_max,
            "process_count_avg": process_count_avg,

            "request_count": request_count,
            "exception_count": exception_count,

            "memory_min_avg": memory_min_avg,
            "memory_max_avg": memory_max_avg,
            "memory_avg": memory_avg,

            "vm_peak_min_avg": vm_peak_min_avg,
            "vm_peak_max_avg": vm_peak_max_avg,
            "vm_peak_avg": vm_peak_avg,

            "threads_current": threads_current,
            "threads_min": threads_min,
            "threads_avg": threads_avg,
            "threads_max": threads_max,

            "response_time_min_avg": human_duration(response_time_min_avg),
            "response_time_max_avg": human_duration(response_time_max_avg),
            "response_time_avg": human_duration(response_time_avg),
            "response_time_sum": human_duration(response_time_sum),

            "user_time_total": human_duration(user_time_total),  # total user mode time
            "system_time_total": human_duration(system_time_total),  # total system mode time
            "processor_time": human_duration(user_time_total + system_time_total),
            "loads": loads,

            "processinfo_version_string": __version__,

            "life_time_min": human_duration(life_time_min),
            "life_time_max": human_duration(life_time_max),
            "life_time_avg": human_duration(life_time_avg),

            "mem_used": mem_used,
            "mem_perc": float(mem_used) / meminfo_dict["MemTotal"] * 100,
            "mem_total": meminfo_dict["MemTotal"],

            "swap_used": swap_used,
            "swap_perc": swap_perc,
            "swap_total": swap_total,

            "updatetime": timesince2(updatetime),

            "script_filename": self.request.META.get("SCRIPT_FILENAME", "???"),
            "server_info": (
                f"{self.request.META.get('SERVER_NAME', '???')}"
                f":{self.request.META.get('SERVER_PORT', '???')}"
            )
        }
        extra_context.update(STATIC_INFORMATIONS)

        try:
            extra_context["loadavg"] = os.getloadavg()
        except OSError as err:
            extra_context["loadavg_err"] = f"[Error: {err}]"

        return super().changelist_view(request, extra_context=extra_context)

    def remove_dead_entries(self, request):
        """ remove all dead ProcessInfo entries """
        start_time = time.monotonic()

        living_pids, dead_pids = ProcessInfo.objects.get_alive_and_dead()

        ProcessInfo.objects.filter(pid__in=dead_pids).delete()

        self.message_user(request, _("Successfully deleted %(count)d dead entries in %(time).1fms.") % {
            "count": len(dead_pids), "time": ((time.monotonic() - start_time) * 1000)
        })
        return HttpResponseRedirect("..")

    def reset(self, request):
        """ do a reset and delete *all* recorded data """
        start_time = time.monotonic()

        count = ProcessInfo.objects.count()
        count += SiteStatistics.objects.count()

        ProcessInfo.objects.all().delete()
        SiteStatistics.objects.all().delete()

        self.message_user(request, _("All recorded data (%(count)d entries) successfully deleted in %(time).1fms.") % {
            "count": count, "time": ((time.monotonic() - start_time) * 1000)
        })
        return HttpResponseRedirect("..")

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            url(r'^remove_dead_entries/$', self.admin_site.admin_view(self.remove_dead_entries)),
            url(r'^reset/$', self.admin_site.admin_view(self.reset)),
        ]
        return my_urls + urls


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
        return human_duration(response_time_avg)
    response_time_avg.short_description = _("Avg response time")

    def request_count(self, obj):
        aggregate_data = self.aggregate_data[obj.site]
        return aggregate_data["request_count__sum"] or 1
    request_count.short_description = _("Requests")

    def exception_count(self, obj):
        aggregate_data = self.aggregate_data[obj.site]
        return aggregate_data["exception_count__sum"] or 0
    exception_count.short_description = _("Exceptions")

    def process_count(self, obj):
        living_process_count = self.aggregate_data[obj.site]["living_process_count"]
        return f"{living_process_count} / {round(obj.process_count_avg, 1):.1f} / {obj.process_count_max}"
    process_count.short_description = _("Living processes (current/avg/max)")

    def threads_info(self, obj):
        aggregate_data = self.aggregate_data[obj.site]
        return mark_safe(
            f'{aggregate_data["threads_min__min"]}'
            f'&nbsp;/&nbsp;'
            f'{aggregate_data["threads_max__max"]:.2f}'
            f'&nbsp;/&nbsp;'
            f'{aggregate_data["threads_avg__avg"]:.2f}'
        )
    threads_info.short_description = _("Threads")
    threads_info.allow_tags = True

    list_display = [
        "site",
        "sum_memory_avg", "sum_vm_peak",
        "response_time_avg", "request_count", "exception_count",
        "process_spawn", "process_count", "threads_info",
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
        return human_duration(obj.response_time_avg)
    response_time_avg2.short_description = _("Avg response time")
    response_time_avg2.admin_order_field = "response_time_avg"

    def response_time_sum2(self, obj):
        return human_duration(obj.response_time_sum)
    response_time_sum2.short_description = _("Total response time")
    response_time_sum2.admin_order_field = "response_time_sum"

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
        if not active and obj.alive:
            obj.alive = False
            obj.save()
            if settings.DEBUG:
                self.message_user(self.request, _("Mark process with pid %r as dead.") % obj.pid)
        return active
    alive2.boolean = True
    alive2.short_description = _("alive")
    alive2.admin_order_field = "alive"

    def threads_info(self, obj):
        return mark_safe(
            f"{obj.threads_min}&nbsp;/&nbsp;{obj.threads_avg:.2f}&nbsp;/&nbsp;{obj.threads_max}"
        )
    threads_info.short_description = _("Threads")

    def user_time_total2(self, obj):
        return human_duration(obj.user_time_total)
    user_time_total2.short_description = _("user time total")
    user_time_total2.admin_order_field = "user_time_total"

    def system_time_total2(self, obj):
        return human_duration(obj.system_time_total)
    system_time_total2.short_description = _("system time total")
    system_time_total2.admin_order_field = "system_time_total"

    list_display = [
        "pid", "alive2", "site", "request_count", "exception_count", "db_query_count_avg",
        "response_time_avg2", "response_time_sum2", "threads_info",

        "user_time_total2", "system_time_total2",

        "memory_avg2", "vm_peak_avg2",
        "start_time2", "lastupdate_time2", "life_time"
    ]
    if not settings.DEBUG:
        del(list_display[list_display.index("db_query_count_avg")])


admin.site.register(ProcessInfo, ProcessInfoAdmin)
