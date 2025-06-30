from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.index, name='home'),
    path('services/', views.services, name='services'),
    path('doctors/', views.doctors, name='doctors'),
    path('contacts/', views.contacts, name='contacts'),
    path('articles/', views.articles, name='articles'),
    path('article/<int:pk>/', views.article_detail, name='article_detail'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register_patient, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('consultation/', views.create_consultation, name='create_consultation'),
    path('consultation/<int:consultation_id>/communication-log/', views.create_or_update_communication_log, name='create_or_update_communication_log'),
    path('get_services_dates/<int:doctor_id>/', views.get_services_dates, name='get_services_dates'),
    path('get_available_times/<int:doctor_id>/<str:date>/', views.get_available_times, name='get_available_times'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)