from django.urls import path
from . import views
from .views import ApplicationDeleteView, ApplicationListView, ApplicationDetailView, ApplicationCreateView, ApplicationUpdateView, ApplicationDeleteView

app_name = 'blog'

urlpatterns = [
    path('', views.home, name='home'),
    path('reg/', views.reg_page, name='reg'),
    path('login/', views.login_page, name='login'),
    path('landing/', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard_page, name='dashboard'),
    path('applications/', ApplicationListView.as_view(), name='application-list'),
    path('application/<int:pk>/', ApplicationDetailView.as_view(), name='application-detail'),
    path('application/create/', ApplicationCreateView.as_view(), name='application-create'),
    path('applications/<int:pk>/update/', ApplicationUpdateView.as_view(), name='application-update'),
    path('applications/<int:app_id>/upload/', views.upload_document, name='document-upload'),
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark-notification-read'),
    path('profile/', views.profile, name='profile'),
    path('auditors/', views.AuditorListView.as_view(), name='auditor-list'),
    path('applications/search/', views.ApplicationSearchView.as_view(), name='application-search'),
    path('application/<int:pk>/delete/', ApplicationDeleteView.as_view(), name='application-delete'),

]