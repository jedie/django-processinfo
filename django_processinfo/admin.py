# coding: utf-8

"""
    models stuff
    ~~~~~~~~~~~~

    :copyleft: 2011 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

from __future__ import division, absolute_import

from django.contrib import admin
from django_processinfo.models import SiteStatistics, ProcessInfo


class SiteStatisticsAdmin(admin.ModelAdmin):
    pass

admin.site.register(SiteStatistics, SiteStatisticsAdmin)


class ProcessInfoAdmin(admin.ModelAdmin):
    pass

admin.site.register(ProcessInfo, ProcessInfoAdmin)
