import debug_toolbar
from django.conf import settings
from django.conf.urls import include, static, url
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView


admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^$', RedirectView.as_view(url='/admin/')),

    url(r'^__debug__/', include(debug_toolbar.urls)),
]
urlpatterns += static.static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
