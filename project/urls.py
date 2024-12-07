from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', include('application.urls')),  # Direct the root URL to the application.urls
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
