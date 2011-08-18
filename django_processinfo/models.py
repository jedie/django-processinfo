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


class BaseModel(models.Model):
    createtime = models.DateTimeField(auto_now_add=True, help_text="Create time")
    lastupdatetime = models.DateTimeField(auto_now=True, help_text="Time of the last change.")

    db_query_count_min = models.PositiveIntegerField(
        help_text=_("Minimum database query count (ony available if settings.DEBUG==True)")
    )
    db_query_count_max = models.PositiveIntegerField(
        help_text=_("Maximum database query count (ony available if settings.DEBUG==True)")
    )
    db_query_count_average = models.PositiveIntegerField(
        help_text=_("Average database query count (ony available if settings.DEBUG==True)")
    )

    request_count = models.PositiveIntegerField(
        help_text=_("How many request answered since self.createtime")
    )

    response_time_min = models.PositiveIntegerField(
        help_text=_("Minimum processing time.")
    )
    response_time_max = models.PositiveIntegerField(
        help_text=_("Maximum processing time.")
    )
    response_time_average = models.PositiveIntegerField(
        help_text=_("Average processing time.")
    )

    # CPU information:

    threads_count = models.PositiveSmallIntegerField()
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

    vm_peak = models.PositiveIntegerField(
        help_text=_('Peak virtual memory size (VmPeak) in Bytes')
    )
    memory_min = models.PositiveIntegerField(
        help_text=_("Minimum Non-paged memory (VmRSS - Resident set size)")
    )
    memory_max = models.PositiveIntegerField(
        help_text=_("Maximum Non-paged memory (VmRSS - Resident set size)")
    )
    memory_average = models.PositiveIntegerField(
        help_text=_("Average Non-paged memory (VmRSS - Resident set size)")
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
        help_text=_("How many processes started since self.createtime")
    )

    process_count_average = models.PositiveSmallIntegerField(
        help_text=_("Average number of living processes.")
    )
    process_count_max = models.PositiveSmallIntegerField(
        help_text=_("Maximum number of living processes.")
    )
    request_count = models.PositiveIntegerField(
        help_text=_("How many request for this site since self.createtime")
    )


class ProcessInfo(BaseModel):
    """
    Information about a running process.
    
    Would be automaticly cleanup by: FIXME
    """
    pid = models.SmallIntegerField(
        primary_key=True,
        help_text=_("process ID.")
    )
    site = models.ForeignKey(Site, default=Site.objects.get_current,
        help_text=_("settings.SITE_ID")
    )




