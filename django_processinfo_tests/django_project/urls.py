import debug_toolbar
from django.conf import settings
from django.conf.urls import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView


admin.autodiscover()

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/')),
    path('admin/', admin.site.urls),
    re_path(r'^__debug__/', include(debug_toolbar.urls)),
]
urlpatterns += static.static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
