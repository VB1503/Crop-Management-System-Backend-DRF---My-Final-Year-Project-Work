
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import index
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include("accounts.urls")),
    path("api/", include("GoogleAuth.urls")),
    path('',include('CRS.urls')),
     path('', index, name='index'),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
