from django.urls import path, include
from event import views  # index view'ini almak için event uygulamasından views'leri import edin

urlpatterns = [
    path('', views.index, name='index'),  # Ana sayfa view'i
    path('', include('event.urls')),  # event uygulaması URL'lerini dahil et
]
