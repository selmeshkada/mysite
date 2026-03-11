from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, SubscriptionPlan, Subscription, Company,
    Category, Transaction, Report, Notification
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Админка для пользователей"""
    list_display = ('email', 'full_name', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('email', 'full_name', 'phone', 'password')
        }),
        ('Статус', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('Даты', {
            'fields': ('last_login', 'date_joined', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'last_login', 'date_joined')


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """Админка для тарифных планов"""
    list_display = ('name', 'price_monthly', 'price_yearly', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('price_monthly',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'features')
        }),
        ('Цены', {
            'fields': ('price_monthly', 'price_yearly')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка для подписок"""
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'plan')
    search_fields = ('user__email', 'user__full_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Пользователь и тариф', {
            'fields': ('user', 'plan')
        }),
        ('Период', {
            'fields': ('start_date', 'end_date')
        }),
        ('Статус', {
            'fields': ('status',)
        }),
    )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Админка для компаний"""
    list_display = ('name', 'inn', 'creator', 'tax_system', 'created_at')
    list_filter = ('tax_system',)
    search_fields = ('name', 'inn', 'creator__email')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('creator', 'name')
        }),
        ('Реквизиты', {
            'fields': ('inn', 'ogrn', 'legal_address')
        }),
        ('Налогообложение', {
            'fields': ('tax_system',)
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Админка для категорий"""
    list_display = ('name', 'type', 'icon')
    list_filter = ('type',)
    search_fields = ('name',)
    ordering = ('type', 'name')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Админка для транзакций"""
    list_display = ('transaction_date', 'company', 'operation_type', 'category', 'amount', 'counterparty')
    list_filter = ('operation_type', 'category', 'transaction_date')
    search_fields = ('description', 'counterparty', 'company__name')
    ordering = ('-transaction_date', '-created_at')
    
    fieldsets = (
        ('Компания и категория', {
            'fields': ('company', 'category', 'operation_type')
        }),
        ('Детали операции', {
            'fields': ('amount', 'counterparty', 'description')
        }),
        ('Даты', {
            'fields': ('transaction_date', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Админка для отчетов"""
    list_display = ('company', 'report_type', 'period_month', 'period_year', 'status', 'created_at')
    list_filter = ('status', 'report_type', 'period_year')
    search_fields = ('company__name',)
    ordering = ('-period_year', '-period_month')
    
    fieldsets = (
        ('Компания и тип', {
            'fields': ('company', 'report_type')
        }),
        ('Период', {
            'fields': ('period_month', 'period_year')
        }),
        ('Статус и файл', {
            'fields': ('status', 'file_path')
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Админка для уведомлений"""
    list_display = ('title', 'user', 'notification_date', 'is_read')
    list_filter = ('is_read', 'notification_date')
    search_fields = ('title', 'content', 'user__email')
    ordering = ('-notification_date',)
    
    fieldsets = (
        ('Получатель', {
            'fields': ('user',)
        }),
        ('Содержание', {
            'fields': ('title', 'content')
        }),
        ('Статус', {
            'fields': ('is_read', 'notification_date')
        }),
    )

    