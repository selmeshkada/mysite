from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, SubscriptionPlan, Subscription, Company,
    Category, Transaction, Report, Notification, CompanyMembership
)


class SubscriptionInline(admin.TabularInline):
    """Подписки пользователя (внутри пользователя)"""
    model = Subscription
    extra = 0
    fields = ('plan', 'status', 'start_date', 'end_date', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True


class CompanyInline(admin.TabularInline):
    """Компании пользователя (внутри пользователя)"""
    model = Company
    extra = 0
    fields = ('name', 'inn', 'tax_system', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True
    fk_name = 'creator'


class CategoryInline(admin.TabularInline):
    """Категории пользователя (внутри пользователя)"""
    model = Category
    extra = 0
    fields = ('name', 'category_type', 'color', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True
    max_num = 50

class NotificationInline(admin.TabularInline):
    """Уведомления пользователя (внутри пользователя)"""
    model = Notification
    extra = 0
    fields = ('title', 'content', 'notification_date', 'is_read')
    readonly_fields = ('notification_date',)
    show_change_link = True


class TransactionInline(admin.TabularInline):
    """Транзакции компании (внутри компании)"""
    model = Transaction
    extra = 0
    fields = ('transaction_date', 'operation_type', 'category', 'amount', 'counterparty')
    readonly_fields = ('created_at',)
    show_change_link = True


class OrderItemInline(admin.TabularInline):
    """Товары в заказе (если добавишь модель Order позже)"""
    # model = OrderItem
    extra = 0
    # fields = ('product', 'price', 'quantity')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Админка для пользователей"""
    list_display = ('email', 'full_name', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'last_login', 'date_joined')
    list_display_links = ('email',)
    filter_horizontal = ('following',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личная информация', {'fields': ('full_name', 'phone', 'avatar')}),
        ('Подписки', {'fields': ('following',)}),
        ('Статус', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'phone', 'password1', 'password2'),
        }),
    )
    
    inlines = [
        SubscriptionInline,
        CompanyInline,
        CategoryInline,
        NotificationInline,
    ]
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'username' in form.base_fields:
            del form.base_fields['username']
        return form

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
    search_fields = ('user__email', 'user__full_name', 'plan__name')
    ordering = ('-created_at',)
    list_display_links = ('user',)
    raw_id_fields = ('user', 'plan')
    
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

class CompanyMembershipInline(admin.TabularInline):
    model = CompanyMembership
    extra = 1
    raw_id_fields = ('user',)
    fields = ('user', 'role', 'joined_at')
    readonly_fields = ('joined_at',)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'inn', 'creator', 'responsible_editor_phone', 'last_edited_at', 'created_at')
    list_filter = ('tax_system', 'created_at', 'ogrn')
    search_fields = ('name', 'inn', 'creator__email', 'responsible_editor__email', 'responsible_editor__phone')
    ordering = ('-created_at',)
    list_display_links = ('name',)
    raw_id_fields = ('creator', 'responsible_editor')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('creator', 'responsible_editor', 'name')
        }),
        ('Реквизиты', {
            'fields': ('inn', 'ogrn', 'legal_address')
        }),
        ('Налогообложение', {
            'fields': ('tax_system',)
        }),
    )
    
    inlines = [CompanyMembershipInline, TransactionInline]
    
    def responsible_editor_phone(self, obj):
        """Отображает почту ответственного редактора"""
        if obj.responsible_editor:
            phone = obj.responsible_editor.phone
            if phone:
                return phone
            return obj.responsible_editor.email
        return "—"
    responsible_editor_phone.short_description = "Ответственный (почта)"
    
    def save_model(self, request, obj, form, change):
        if change:
            obj.responsible_editor = request.user
        else:
            obj.creator = request.user
        super().save_model(request, obj, form, change)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Админка для категорий"""
    list_display = ('name', 'category_type', 'user_link', 'icon', 'created_at')
    list_filter = ('category_type', 'user')
    search_fields = ('name', 'user__email', 'user__full_name')
    ordering = ('user__email', 'name')
    list_display_links = ('name',)
    raw_id_fields = ('user',)
    
    def user_link(self, obj):
            if obj.user:
                return f"{obj.user.email} ({obj.user.phone or '—'})"
            return "—"
    user_link.short_description = "Пользователь"

    @admin.display(description='Тип', ordering='category_type')
    def colored_type(self, obj):
        colors = {'income': 'Доход', 'expense': 'Расход'}
        return colors.get(obj.category_type, '⚪')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Админка для транзакций"""
    list_display = ('transaction_date', 'company', 'operation_type', 'category', 'amount', 'counterparty')
    list_filter = ('operation_type', 'category', 'transaction_date')
    date_hierarchy = 'transaction_date'
    list_display_links = ('transaction_date',)
    raw_id_fields = ('company', 'category')
    search_fields = ('description', 'counterparty', 'company__name')
    ordering = ('-transaction_date', '-created_at')
    readonly_fields = ('created_at',)
    
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


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Админка для отчетов"""
    list_display = ('company', 'report_type', 'period_month', 'period_year', 'status', 'created_at')
    list_filter = ('status', 'report_type', 'period_year')
    date_hierarchy = 'created_at'
    search_fields = ('company__name',)
    ordering = ('-period_year', '-period_month')
    list_display_links = ('company',)
    raw_id_fields = ('company',)
    
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
    list_display = ('title', 'user', 'notification_date', 'is_read', 'read_status')
    list_filter = ('is_read', 'notification_date')
    search_fields = ('title', 'content', 'user__email')
    ordering = ('-notification_date',)
    date_hierarchy = 'notification_date'
    list_display_links = ('title',)
    raw_id_fields = ('user',)
    
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
    
    @admin.display(description='Прочитано', boolean=True)
    def read_status(self, obj):
        return obj.is_read
    
