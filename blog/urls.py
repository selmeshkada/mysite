from django.urls import path
from . import views
from .views import (
    # Аутентификация и страницы
    reg_page, login_page, logout_view, landing_page,
    dashboard_page, finance_page, reports_page,
    
    # API
    dashboard_data,
    
    # Компании
    CompanyListView, CompanyDetailView, CompanyCreateView,
    CompanyUpdateView, CompanyDeleteView,
    
    # Категории
    CategoryListView, CategoryCreateView, CategoryUpdateView, CategoryDeleteView,
    
    # Транзакции
    TransactionListView, TransactionDetailView, TransactionCreateView,
    TransactionUpdateView, TransactionDeleteView,
    
    # Отчеты
    ReportListView, ReportCreateView, ReportDetailView, ReportDeleteView,
    generate_report,
    
    # Подписки
    SubscriptionPlanListView, SubscriptionPlanDetailView,
    subscribe, UserSubscriptionListView,
    
    # Уведомления
    NotificationListView, mark_notification_read, mark_all_notifications_read,
    
    # Профиль
    profile_view, profile_edit,
)

app_name = 'blog'

urlpatterns = [
    # ============== ПУБЛИЧНЫЕ СТРАНИЦЫ ==============
    path('', landing_page, name='landing'),
    path('reg/', reg_page, name='reg'),
    path('login/', login_page, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # ============== ЛИЧНЫЙ КАБИНЕТ ==============
    path('dashboard/', dashboard_page, name='dashboard'),
    path('finance/', finance_page, name='finance'),
    path('reports/', reports_page, name='reports'),
    
    # ============== API ==============
    path('api/dashboard-data/', dashboard_data, name='dashboard-data'),
    
    # ============== КОМПАНИИ ==============
    path('companies/', CompanyListView.as_view(), name='company-list'),
    path('companies/<int:pk>/', CompanyDetailView.as_view(), name='company-detail'),
    path('companies/create/', CompanyCreateView.as_view(), name='company-create'),
    path('companies/<int:pk>/update/', CompanyUpdateView.as_view(), name='company-update'),
    path('companies/<int:pk>/delete/', CompanyDeleteView.as_view(), name='company-delete'),
    
    # ============== КАТЕГОРИИ ==============
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/update/', CategoryUpdateView.as_view(), name='category-update'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category-delete'),
    
    # ============== ТРАНЗАКЦИИ ==============
    path('transactions/', TransactionListView.as_view(), name='transaction-list'),
    path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('transactions/create/', TransactionCreateView.as_view(), name='transaction-create'),
    path('transactions/<int:pk>/update/', TransactionUpdateView.as_view(), name='transaction-update'),
    path('transactions/<int:pk>/delete/', TransactionDeleteView.as_view(), name='transaction-delete'),
    
    # ============== ОТЧЕТЫ ==============
    path('reports/list/', ReportListView.as_view(), name='report-list'),
    path('reports/<int:pk>/', ReportDetailView.as_view(), name='report-detail'),
    path('reports/create/', ReportCreateView.as_view(), name='report-create'),
    path('reports/<int:pk>/delete/', ReportDeleteView.as_view(), name='report-delete'),
    path('reports/generate/', generate_report, name='report-generate'),
    
    # ============== ПОДПИСКИ ==============
    path('plans/', SubscriptionPlanListView.as_view(), name='plan-list'),
    path('plans/<int:pk>/', SubscriptionPlanDetailView.as_view(), name='plan-detail'),
    path('subscribe/<int:plan_id>/', subscribe, name='subscribe'),
    path('my-subscriptions/', UserSubscriptionListView.as_view(), name='user-subscriptions'),
    
    # ============== УВЕДОМЛЕНИЯ ==============
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', mark_notification_read, name='notification-read'),
    path('notifications/read-all/', mark_all_notifications_read, name='notifications-read-all'),
    
    # ============== ПРОФИЛЬ ==============
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', profile_edit, name='profile-edit'),
]

