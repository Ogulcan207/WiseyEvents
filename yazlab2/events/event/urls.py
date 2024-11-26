from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/user', views.user_login, name='login_user'),
    path('login/admin', views.admin_login, name='login_admin'),
    path('admin/dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('user/dashboard', views.user_dashboard, name='user_dashboard'),
    path('password/reset', views.password_reset, name='password_reset'),
    path('password/reset/confirmation', views.password_reset_confirmation, name='password_reset_confirmation'),
    path('signup', views.signup, name='signup'),
    path('update_profile', views.update_profile, name='update_profile'),
    path('edit_event/<int:event_id>/', views.edit_event, name='edit_event'),
]
