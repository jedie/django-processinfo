from django.contrib.auth.models import User
from django.test import TestCase
from model_bakery import baker

from django_processinfo.models import ProcessInfo, SiteStatistics


class AdminAnonymousTests(TestCase):
    """
    Anonymous will be redirected to the login page.
    """

    def test_login_en(self):
        response = self.client.get('/admin/', HTTP_ACCEPT_LANGUAGE='en')
        self.assertRedirects(response, expected_url='/admin/login/?next=/admin/')

    def test_login_de(self):
        response = self.client.get('/admin/', HTTP_ACCEPT_LANGUAGE='de')
        self.assertRedirects(response, expected_url='/admin/login/?next=/admin/')


class ProcessinfoAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = baker.make(
            User, is_staff=True, is_active=True, is_superuser=True
        )

    def test_sitestatistics(self):
        self.client.force_login(self.superuser)

        assert SiteStatistics.objects.count() == 0
        assert ProcessInfo.objects.count() == 0

        response = self.client.get('/admin/django_processinfo/sitestatistics/')
        self.assertTemplateUsed(response, 'admin/django_processinfo/change_list.html')

        response = response.content.decode("utf-8")
        self.assertInHTML(
            '<title>Select Site statistics to change | Django site admin</title>',
            response
        )
        self.assertInHTML('<h2>System information</h2>', response)
        self.assertInHTML('<dt>Living processes (current/avg/max)</dt>', response)
        assert 'django-processinfo:' in response

        assert SiteStatistics.objects.count() == 1
        assert ProcessInfo.objects.count() == 1

    def test_processinfo(self):
        self.client.force_login(self.superuser)

        assert SiteStatistics.objects.count() == 0
        assert ProcessInfo.objects.count() == 0

        response = self.client.get('/admin/django_processinfo/processinfo/')
        self.assertTemplateUsed(response, 'admin/django_processinfo/change_list.html')

        response = response.content.decode("utf-8")
        self.assertInHTML(
            '<title>Select Process statistics to change | Django site admin</title>',
            response
        )
        self.assertInHTML('<h2>System information</h2>', response)
        self.assertInHTML('<dt>Living processes (current/avg/max)</dt>', response)
        assert 'django-processinfo:' in response

        assert SiteStatistics.objects.count() == 1
        assert ProcessInfo.objects.count() == 1
