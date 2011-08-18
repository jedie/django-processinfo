# coding: utf-8

"""
    models stuff
    ~~~~~~~~~~~~

    :copyleft: 2011 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

from __future__ import division, absolute_import

from django.db import models
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _


class BaseModel(models.Model):
    create_time = models.DateTimeField(auto_now_add=True, help_text="Create time")
    lastupdate_time = models.DateTimeField(auto_now=True, help_text="Time of the last change.")

    db_query_count_min = models.PositiveIntegerField(
        verbose_name=_("Min db queries"),
        help_text=_("Minimum database query count (ony available if settings.DEBUG==True)")
    )
    db_query_count_max = models.PositiveIntegerField(
        verbose_name=_("Max db queries"),
        help_text=_("Maximum database query count (ony available if settings.DEBUG==True)")
    )
    db_query_count_average = models.PositiveIntegerField(
        verbose_name=_("Avg db queries"),
        help_text=_("Average database query count (ony available if settings.DEBUG==True)")
    )

    request_count = models.PositiveIntegerField(
        help_text=_("How many request answered since self.create_time")
    )

    response_time_min = models.FloatField(
        help_text=_("Minimum processing time.")
    )
    response_time_max = models.FloatField(
        help_text=_("Maximum processing time.")
    )
    response_time_average = models.FloatField(
        help_text=_("Average processing time.")
    )

    # CPU information:

    threads_average = models.FloatField()
    threads_min = models.PositiveSmallIntegerField()
    threads_max = models.PositiveSmallIntegerField()

    ru_utime_total = models.FloatField(
        help_text=_("total user mode time")
    )
    ru_stime_total = models.FloatField(
        help_text=_("total system mode time")
    )
    ru_utime_min = models.FloatField(
        help_text=_("Minimum user mode time")
    )
    ru_stime_min = models.FloatField(
        help_text=_("Minimum system mode time")
    )
    ru_utime_max = models.FloatField(
        help_text=_("Maximum user mode time")
    )
    ru_stime_max = models.FloatField(
        help_text=_("Maximum system mode time")
    )

    # RAM consumption:

    vm_peak_max = models.PositiveIntegerField(
        help_text=_('Maximum Peak virtual memory size (VmPeak) in Bytes')
    )
    memory_min = models.PositiveIntegerField(
        help_text=_("Minimum Non-paged memory (VmRSS - Resident set size) in Bytes")
    )
    memory_max = models.PositiveIntegerField(
        help_text=_("Maximum Non-paged memory (VmRSS - Resident set size) in Bytes")
    )
    memory_average = models.PositiveIntegerField(
        help_text=_("Average Non-paged memory (VmRSS - Resident set size) in Bytes")
    )

    class Meta:
        abstract = True



class SiteStatistics(BaseModel):
    """
    Obverall statistics seperated per settings.SITE_ID
    """
    site = models.ForeignKey(Site, default=Site.objects.get_current,
        primary_key=True,
        help_text=_("settings.SITE_ID")
    )

    total_processes = models.PositiveIntegerField(
        help_text=_("How many processes started since self.create_time")
    )
    process_count_average = models.PositiveSmallIntegerField(
        help_text=_("Average number of living processes.")
    )
    process_count_max = models.PositiveSmallIntegerField(
        help_text=_("Maximum number of living processes.")
    )

    class Meta:
        verbose_name_plural = verbose_name = "Site statistics"
        ordering = ("-lastupdate_time",)


class ProcessInfo(BaseModel):
    """
    Information about a running process.
    """
    pid = models.SmallIntegerField(
        primary_key=True,
        help_text=_("process ID.")
    )
    site = models.ForeignKey(Site, default=Site.objects.get_current,
        help_text=_("settings.SITE_ID")
    )

    class Meta:
        verbose_name_plural = verbose_name = "Process statistics"
        ordering = ("-lastupdate_time",)



