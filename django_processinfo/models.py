"""
    models stuff
    ~~~~~~~~~~~~

    :copyleft: 2011-2018 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import os

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_processinfo.utils.average import average


class BaseModel(models.Model):
    start_time = models.DateTimeField(auto_now_add=True, help_text="Create time")
    lastupdate_time = models.DateTimeField(auto_now=True, help_text="Time of the last change.")

    class Meta:
        abstract = True


class SiteStatistics(BaseModel):
    """
    Overall statistics separated per settings.SITE_ID
    """
    site = models.OneToOneField(
        Site, primary_key=True, db_index=True, default=settings.SITE_ID,
        on_delete=models.CASCADE,
        help_text=_("settings.SITE_ID")
    )

    process_spawn = models.PositiveIntegerField(
        default=1,
        help_text=_("Total number of processes spawend (approximated)")
    )
    process_count_avg = models.FloatField(
        default=1.0,
        help_text=_("Average number of living processes. (approximated)")
    )
    process_count_max = models.PositiveSmallIntegerField(
        default=1, help_text=_("Maximum number of living processes. (approximated)"))

    def update_informations(self):
        living_pids = ProcessInfo.objects.living_processes(site=self.site)
        living_process_count = len(living_pids)

        self.process_count_avg = average(
            self.process_count_avg, living_process_count, self.process_spawn
        )
        if self.process_count_avg < 1:
            self.process_count_avg = 1  # Less than one is not possible ;)

        self.process_count_max = max([self.process_count_max, living_process_count])
        return living_pids

    def __unicode__(self):
        return f"SiteStatistics for {self.site}"

    class Meta:
        verbose_name_plural = verbose_name = "Site statistics"
        ordering = ("-lastupdate_time",)


class ProcessInfoManager(models.Manager):
    def get_alive_and_dead(self, site=None):
        """ returns two list, with alive and a list with dead pids """
        if site is None:
            queryset = self.all()
        else:
            queryset = self.filter(site=site)

        pids = queryset.values_list("pid", flat=True)

        living_pids = []
        dead_pids = []
        proc_dirlist = os.listdir("/proc/")
        for pid in pids:
            if not str(pid) in proc_dirlist:
                dead_pids.append(pid)
            else:
                living_pids.append(pid)

        return living_pids, dead_pids

    def living_processes(self, site=None):
        """
        returns a list of pids from processes which are really alive.
        Mark dead ProcessInfo instances.
        """
        living_pids, dead_pids = self.get_alive_and_dead(site)

        if site is None:
            queryset = self.all()
        else:
            queryset = self.filter(site=site)

        queryset.filter(pid__in=dead_pids).update(alive=False)

        if site is not None and site == Site.objects.get_current():
            # Assume that the current PID is in living pid list.
            # (For calculating the current living process count)
            # The ProcessInfo() instance doesn't exist in the first Request,
            # because it's created in middleware.process_response()!
            current_pid = os.getpid()
            if current_pid not in living_pids:
                living_pids.append(current_pid)

        return living_pids


class ProcessInfo(BaseModel):
    """
    Information about a running process.
    """
    objects = ProcessInfoManager()

    pid = models.SmallIntegerField(
        primary_key=True, db_index=True,
        help_text=_("process ID.")
    )
    alive = models.BooleanField(
        null=True,
        help_text=_(
            "Is this process dead (==False)?"
            " *Important:* alive is never==True! If alive==None: State unknown!"
            " (We don't check the state in every request!)"
        )
    )
    site = models.ForeignKey(
        Site, default=settings.SITE_ID,
        on_delete=models.CASCADE,
        help_text=_("settings.SITE_ID")
    )

    db_query_count_min = models.PositiveIntegerField(
        verbose_name=_("Min db queries"),
        help_text=_("Minimum database query count (ony available if settings.DEBUG==True)")
    )
    db_query_count_max = models.PositiveIntegerField(
        verbose_name=_("Max db queries"),
        help_text=_("Maximum database query count (ony available if settings.DEBUG==True)")
    )
    db_query_count_avg = models.PositiveIntegerField(
        verbose_name=_("Avg db queries"),
        help_text=_("Average database query count (ony available if settings.DEBUG==True)")
    )

    request_count = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Requests"),
        help_text=_("How many request answered since self.start_time")
    )
    exception_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Exceptions"),
        help_text=_("How many requests led to a exception.")
    )

    response_time_min = models.FloatField(
        help_text=_("Minimum processing time.")
    )
    response_time_max = models.FloatField(
        help_text=_("Maximum processing time.")
    )
    response_time_avg = models.FloatField(
        help_text=_("Average processing time.")
    )
    response_time_sum = models.FloatField(
        help_text=_("Total processing time.")
    )

    # CPU information:

    threads_avg = models.FloatField(
        help_text=_("Average number of threads per process."),
    )
    threads_min = models.PositiveSmallIntegerField()
    threads_max = models.PositiveSmallIntegerField()

    user_time_total = models.FloatField(
        help_text=_("total user mode time")
    )
    system_time_total = models.FloatField(
        help_text=_("total system mode time")
    )
    user_time_min = models.FloatField(
        help_text=_("Minimum user mode time")
    )
    system_time_min = models.FloatField(
        help_text=_("Minimum system mode time")
    )
    user_time_max = models.FloatField(
        help_text=_("Maximum user mode time")
    )
    system_time_max = models.FloatField(
        help_text=_("Maximum system mode time")
    )

    # RAM consumption:

    vm_peak_min = models.PositiveIntegerField(
        help_text=_('Minimum Peak virtual memory size (VmPeak) in Bytes')
    )
    vm_peak_max = models.PositiveIntegerField(
        help_text=_('Maximum Peak virtual memory size (VmPeak) in Bytes')
    )
    vm_peak_avg = models.PositiveIntegerField(
        help_text=_('Average Peak virtual memory size (VmPeak) in Bytes')
    )

    memory_min = models.PositiveIntegerField(
        help_text=_("Minimum Non-paged memory (VmRSS - Resident set size) in Bytes")
    )
    memory_max = models.PositiveIntegerField(
        help_text=_("Maximum Non-paged memory (VmRSS - Resident set size) in Bytes")
    )
    memory_avg = models.PositiveIntegerField(
        help_text=_("Average Non-paged memory (VmRSS - Resident set size) in Bytes")
    )

    class Meta:
        verbose_name_plural = verbose_name = "Process statistics"
        ordering = ("-lastupdate_time",)
