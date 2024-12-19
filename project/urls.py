from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from application.views import custom_404_view

urlpatterns = [
    path('', include('application.urls')),
    path('adminapp/', include('adminapp.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = custom_404_view

if settings.DEBUG is False:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)