from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.home, name='home'),
    path('applications/', views.ApplicationListView.as_view(), name='application-list'),
    path('applications/<int:pk>/', views.ApplicationDetailView.as_view(), name='application-detail'),
    path('applications/new/', views.ApplicationCreateView.as_view(), name='application-create'),
    path('applications/<int:pk>/update/', views.ApplicationUpdateView.as_view(), name='application-update'),
    path('applications/<int:app_id>/upload/', views.upload_document, name='document-upload'),
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark-notification-read'),
    path('profile/', views.profile, name='profile'),
    path('auditors/', views.AuditorListView.as_view(), name='auditor-list'),
    path('applications/search/', views.ApplicationSearchView.as_view(), name='application-search'),
]