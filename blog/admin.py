from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Organization, AuditorCompany, Application, Document, Notification, AuditLog

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone_number', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('username', 'email', 'phone_number')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('email', 'phone_number', 'role')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'role', 'password1', 'password2'),
        }),
    )
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)

admin.site.register(User, CustomUserAdmin)

class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'inn', 'last_audit_status')
    list_filter = ('filials', 'legal_cases', 'tax_audits')
    search_fields = ('name', 'inn', 'address')
    raw_id_fields = ('user',)
    
    @admin.display(description="Статус последнего аудита")
    def last_audit_status(self, obj):
        if obj.last_audit_date:
            return f"Аудит проведен {obj.last_audit_date}"
        return "Аудит не проводился"

admin.site.register(Organization, OrganizationAdmin)

class AuditorCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'ogrn', 'quality_control_status')
    list_filter = ('quality_control',)
    search_fields = ('name', 'ogrn', 'certificate_number', 'au_fio')
    raw_id_fields = ('user',)
    
    @admin.display(description="Контроль качества", boolean=True)
    def quality_control_status(self, obj):
        return obj.quality_control

admin.site.register(AuditorCompany, AuditorCompanyAdmin)

class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    readonly_fields = ('upload_date',)
    fields = ('name', 'type', 'file', 'uploaded_by', 'upload_date')

class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'auditor_company', 'status_with_color', 'date', 'audit_duration')
    list_filter = ('status', 'date', 'auditor_company')
    search_fields = ('organization__name', 'auditor_company__name', 'comments')
    raw_id_fields = ('organization', 'auditor_company')
    date_hierarchy = 'date'
    inlines = [DocumentInline]
    readonly_fields = ('date',)
    list_display_links = ('id', 'organization')
    
    @admin.display(description="Статус")
    def status_with_color(self, obj):
        color = obj.get_status_color()
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    @admin.display(description="Длительность аудита")
    def audit_duration(self, obj):
        if obj.audit_start and obj.audit_end:
            duration = (obj.audit_end - obj.audit_start).days
            return f"{duration} дней"
        return "Не указано"

admin.site.register(Application, ApplicationAdmin)

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'application_link', 'type', 'uploaded_by', 'upload_date')
    list_filter = ('type', 'upload_date')
    search_fields = ('name', 'application__id')
    raw_id_fields = ('application', 'uploaded_by')
    date_hierarchy = 'upload_date'
    
    @admin.display(description="Заявка")
    def application_link(self, obj):
        return format_html(
            '<a href="/admin/yourapp/application/{}/change/">#{}</a>',
            obj.application.id,
            obj.application.id
        )

admin.site.register(Document, DocumentAdmin)

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_to', 'short_message', 'is_read', 'sent_date')
    list_filter = ('is_read', 'sent_date')
    search_fields = ('message', 'user_to__username')
    raw_id_fields = ('user_to',)
    date_hierarchy = 'sent_date'
    readonly_fields = ('sent_date',)
    
    @admin.display(description="Сообщение")
    def short_message(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message

admin.site.register(Notification, NotificationAdmin)

class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'table_name', 'record_id', 'action_type')
    list_filter = ('action_type', 'table_name', 'action_time')
    search_fields = ('user__username', 'table_name', 'record_id')
    date_hierarchy = 'action_time'
    readonly_fields = ('action_time', 'user', 'table_name', 'record_id', 'action_type', 'old_data', 'new_data')

admin.site.register(AuditLog, AuditLogAdmin)