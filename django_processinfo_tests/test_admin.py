import datetime
import time
from unittest import mock

from bx_django_utils.test_utils.datetime import MockDatetimeGenerator
from bx_django_utils.test_utils.html_assertion import HtmlAssertionMixin
from bx_py_utils.test_utils.time import MockTimeMonotonicGenerator
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from django_processinfo.models import ProcessInfo, SiteStatistics


class AdminAnonymousTests(TestCase):
    """
    Anonymous will be redirected to the login page.
    """

    def test_login_en(self):
        response = self.client.get('/admin/', HTTP_ACCEPT_LANGUAGE='en')
        self.assertRedirects(response, expected_url='/admin/login/?next=/admin/')
        response = self.client.get('/admin/login/?next=/admin/', HTTP_ACCEPT_LANGUAGE='en')
        self.assertTemplateUsed(response, 'admin/login.html')
        content_length = int(response['Content-Length'])
        response = response.content.decode("utf-8")
        assert '<p class="django-processinfo"><small>django-processinfo:' in response
        assert response.endswith('%)</small></p></body>\n</html>\n')
        assert len(response) == content_length

    def test_login_de(self):
        response = self.client.get('/admin/', HTTP_ACCEPT_LANGUAGE='de')
        self.assertRedirects(response, expected_url='/admin/login/?next=/admin/')
        response = self.client.get('/admin/login/?next=/admin/', HTTP_ACCEPT_LANGUAGE='de')
        self.assertTemplateUsed(response, 'admin/login.html')
        response = response.content.decode("utf-8")
        assert '<p class="django-processinfo"><small>django-processinfo:' in response
        assert response.endswith('%)</small></p></body>\n</html>\n')


class ProcessinfoAdminTestCase(HtmlAssertionMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = baker.make(
            User, is_staff=True, is_active=True, is_superuser=True
        )

    @mock.patch.object(timezone, 'now', MockDatetimeGenerator(datetime.timedelta(minutes=1)))
    @mock.patch.object(time, 'monotonic', MockTimeMonotonicGenerator())
    def test_sitestatistics(self):
        self.client.force_login(self.superuser)

        assert SiteStatistics.objects.count() == 0
        assert ProcessInfo.objects.count() == 0

        response = self.client.get('/admin/django_processinfo/sitestatistics/')
        self.assertTemplateUsed(response, 'admin/django_processinfo/change_list.html')

        self.assert_html_parts(
            response,
            parts=(
                '<title>Select Site statistics to change | Django site admin</title>',
                '<h2>System information</h2>',
                '<dt>Living processes (current/avg/max)</dt>',
                '<small>django-processinfo: 1000.0 ms of 1000.0 ms (100.0%)</small>',
            ),
        )
        assert SiteStatistics.objects.count() == 1
        assert ProcessInfo.objects.count() == 1

    @mock.patch.object(timezone, 'now', MockDatetimeGenerator(datetime.timedelta(minutes=1)))
    @mock.patch.object(time, 'monotonic', MockTimeMonotonicGenerator())
    def test_processinfo(self):
        self.client.force_login(self.superuser)

        assert SiteStatistics.objects.count() == 0
        assert ProcessInfo.objects.count() == 0

        response = self.client.get('/admin/django_processinfo/processinfo/')
        self.assertTemplateUsed(response, 'admin/django_processinfo/change_list.html')

        self.assert_html_parts(
            response,
            parts=(
                '<title>Select Process statistics to change | Django site admin</title>',
                '<h2>System information</h2>',
                '<dt>Living processes (current/avg/max)</dt>',
                '<small>django-processinfo: 1000.0 ms of 1000.0 ms (100.0%)</small>',
            ),
        )
        assert SiteStatistics.objects.count() == 1
        assert ProcessInfo.objects.count() == 1
