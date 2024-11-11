from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Ana sayfa
    path('login/admin', views.admin_login, name='loginadmin'),  # Admin giriş sayfası
    path('login/user', views.user_login, name='loginuser'),  # Kullanıcı giriş sayfası
    path('signup/', views.signup, name='signup'),  # Yeni kullanıcı kayıt sayfası
    path('password_reset/', views.password_reset, name='password_reset'),  # Şifre sıfırlama sayfası
    path('dashboard/admin', views.admin_dashboard, name='admin_dashboard'),  # Admin dashboard
    path('dashboard/user', views.user_dashboard, name='user_dashboard'),  # Kullanıcı dashboard
]
