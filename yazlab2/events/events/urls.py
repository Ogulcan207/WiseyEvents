from django.contrib import admin
from django.urls import path, include
from . import views  

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin paneli
    path('event/', include('event.urls')),  # event uygulaması URL'lerini dahil et
]
