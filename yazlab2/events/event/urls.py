from django.contrib import admin
from django.urls import path
from events import views  # Eğer uygulamanızın adı 'events' ise

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),  # İlk sayfa
    path('login/', views.login_view, name='login'),  # Kullanıcı giriş sayfası
    path('signup/', views.signup_view, name='signup'),  # Yeni kullanıcı kaydı sayfası
    path('password_reset/', views.password_reset_view, name='password_reset'),  # Şifre sıfırlama
]
