from django.urls import path
from . import views
from .views import delete_event, all_events, join_event, password_reset 
urlpatterns = [
    path('', views.index, name='index'),
    path('login/user', views.user_login, name='login_user'),
    path('login/admin', views.admin_login, name='login_admin'),
    path('admin/dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('user/dashboard', views.user_dashboard, name='user_dashboard'),
    path('password/reset/', password_reset, name='password_reset'),
    path('password/reset/confirmation', views.password_reset_confirmation, name='password_reset_confirmation'),
    path('signup', views.signup, name='signup'),
    path('edit_event/<int:event_id>/', views.edit_event, name='edit_event'),
    path('messages/<int:event_id>/', views.event_messages, name='event_messages'),
    path("maps/<int:event_id>/", views.maps, name="maps"),
    path('profile/', views.update_profile, name='profile'),
    path('create_event/', views.create_event, name='create_event'),
    path('event/delete/<int:event_id>/', delete_event, name='delete_event'),  # Silme URL'si
    path('all_events/', all_events, name='all_events'),  # Tüm etkinlikler URL'si
    path('event/join/<int:event_id>/', join_event, name='join_event'),  # Katılma URL'si
    path('admin/delete_event/<int:event_id>/', views.delete_event_admin, name='delete_event_admin'),
    path('approve-event/<int:event_id>/', views.approve_event, name='approve_event'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('disapprove-event/<int:event_id>/', views.disapprove_event, name='disapprove_event'),
    path('edit_event_admin/<int:event_id>/', views.edit_event_admin, name='edit_event_admin'),
]
