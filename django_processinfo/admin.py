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

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext as _

from django_processinfo.models import SiteStatistics, ProcessInfo
from django_processinfo.utils.timesince import timesince2
from django.conf import settings



class BaseModelAdmin(admin.ModelAdmin):
    def create_time2(self, obj):
        return timesince2(obj.create_time)
    create_time2.short_description = _("create time")
    create_time2.admin_order_field = "create_time"

    def lastupdate_time2(self, obj):
        return timesince2(obj.lastupdate_time)
    lastupdate_time2.short_description = _("last update")
    lastupdate_time2.admin_order_field = "lastupdatetime"

    def life_time(self, obj):
        return timesince2(obj.create_time, obj.lastupdate_time)
    life_time.short_description = _("life time")

    def response_time_average2(self, obj):
        return u"%.1fms" % (obj.response_time_average * 1000)
    response_time_average2.short_description = _("Avg response time")
    response_time_average2.admin_order_field = "response_time_average"

    def memory_average2(self, obj):
        return filesizeformat(obj.memory_average)
    memory_average2.short_description = _("Avg memory")
    memory_average2.admin_order_field = "memory_average"

    def vm_peak_max2(self, obj):
        return filesizeformat(obj.vm_peak_max)
    vm_peak_max2.short_description = _("VmPeak")
    vm_peak_max2.admin_order_field = "vm_peak_max"


class SiteStatisticsAdmin(BaseModelAdmin):
    list_display = [
        "site", "request_count", "db_query_count_average",
        "response_time_average2",
        "memory_average2", "vm_peak_max2",
        "create_time2", "lastupdate_time2", "life_time"
    ]
    if not settings.DEBUG:
        del(list_display[list_display.index("db_query_count_average")])

admin.site.register(SiteStatistics, SiteStatisticsAdmin)


class ProcessInfoAdmin(BaseModelAdmin):
    def active(self, obj):
        return os.path.exists("/proc/%i/status" % obj.pid)
    active.boolean = True

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
        "pid", "active", "site", "request_count", "db_query_count_average",
        "response_time_average2",
        "memory_average2", "vm_peak_max2",
        "create_time2", "lastupdate_time2", "life_time"
    ]
    if not settings.DEBUG:
        del(list_display[list_display.index("db_query_count_average")])
    actions = [remove_dead_entries]

admin.site.register(ProcessInfo, ProcessInfoAdmin)
