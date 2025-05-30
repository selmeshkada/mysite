from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator, RegexValidator

class User(AbstractUser):
    ROLE_CHOICES = [
        ('Организация', 'Организация'),
        ('Аудитор', 'Аудитор'),
        ('Администратор', 'Администратор'),
    ]
    
    # Переопределяем стандартные поля, чтобы соответствовать вашей БД
    username = models.CharField(max_length=255, unique=True, verbose_name="Логин")
    password = models.CharField(max_length=128, verbose_name="Пароль")  # Django хранит хеш
    email = models.EmailField(unique=True, verbose_name="Email")
    phone_number = models.CharField(
        max_length=11,
        unique=True,
        validators=[MinLengthValidator(11), RegexValidator(r'^[0-9]*$')],
        verbose_name="Телефон"
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, verbose_name="Роль")
    
    # Убираем неиспользуемые поля из AbstractUser
    first_name = None
    last_name = None
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
    
    def __str__(self):
        return f"{self.username} ({self.role})"

class Organization(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, verbose_name="Пользователь")
    name = models.CharField(max_length=255, verbose_name="Название")
    address = models.TextField(verbose_name="Адрес", blank=True, null=True)
    inn = models.CharField(
        max_length=12,
        validators=[RegexValidator(r'^[0-9]*$')],
        verbose_name="ИНН",
        blank=True,
        null=True
    )
    filials = models.BooleanField(default=False, verbose_name="Есть филиалы")
    legal_cases = models.BooleanField(default=False, verbose_name="Судебные дела")
    tax_audits = models.BooleanField(default=False, verbose_name="Налоговые проверки")
    last_audit_date = models.DateField(verbose_name="Дата последнего аудита", blank=True, null=True)
    
    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"
    
    def __str__(self):
        return self.name

class AuditorCompany(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, verbose_name="Пользователь")
    name = models.CharField(max_length=255, verbose_name="Название")
    address = models.TextField(verbose_name="Адрес")
    postal_address = models.TextField(verbose_name="Почтовый адрес", blank=True, null=True)
    ogrn = models.CharField(max_length=13, verbose_name="ОГРН")
    quality_control = models.BooleanField(default=True, verbose_name="Контроль качества")
    certificate_number = models.CharField(max_length=50, verbose_name="Номер сертификата")
    au_fio = models.CharField(max_length=255, verbose_name="ФИО аудитора")
    
    class Meta:
        verbose_name = "Аудиторская компания"
        verbose_name_plural = "Аудиторские компании"
    
    def __str__(self):
        return self.name

class Application(models.Model):
    STATUS_CHOICES = [
        ('На рассмотрении', 'На рассмотрении'),
        ('Принято', 'Принято'),
        ('Отклонено', 'Отклонено'),
        ('Завершено', 'Завершено'),
    ]
    
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, verbose_name="Организация")
    auditor_company = models.ForeignKey(
    'AuditorCompany', 
    on_delete=models.CASCADE, 
    verbose_name="Аудиторская компания",
    blank=True,  # Разрешает пустое значение в форме
    null=True   # Разрешает NULL в базе данных
)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='На рассмотрении', verbose_name="Статус")
    file = models.FileField(upload_to='applications/', verbose_name="Файл", blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    audit_start = models.DateField(verbose_name="Дата начала аудита", blank=True, null=True)
    audit_end = models.DateField(verbose_name="Дата окончания аудита", blank=True, null=True)
    comments = models.TextField(verbose_name="Комментарии", blank=True, null=True)
    analysis_result = models.TextField(verbose_name="Результат анализа", blank=True, null=True)
    
    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ['-date']
    
    def __str__(self):
        return f"Заявка #{self.id} от {self.organization}"
    
    def get_status_color(self):
        if self.status == 'Завершено':
            return 'green'
        elif self.status == 'Отклонено':
            return 'red'
        elif self.status == 'Принято':
            return 'blue'
        return 'gray'
    get_status_color.short_description = "Цвет статуса"

class Document(models.Model):
    FILE_TYPES = [
        ('pdf', 'PDF'),
        ('xlsx', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    application = models.ForeignKey('Application', on_delete=models.CASCADE, verbose_name="Заявка")
    name = models.CharField(max_length=300, verbose_name="Название")
    type = models.CharField(max_length=10, choices=FILE_TYPES, verbose_name="Тип файла")
    uploaded_by = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name="Загрузил")
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    file = models.FileField(upload_to='documents/', verbose_name="Файл")
    
    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        ordering = ['-upload_date']
    
    def __str__(self):
        return self.name

class Notification(models.Model):
    user_to = models.ForeignKey('User', on_delete=models.CASCADE, related_name='notifications', verbose_name="Получатель")
    message = models.TextField(verbose_name="Сообщение")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    sent_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")
    
    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-sent_date']
    
    def __str__(self):
        return f"Уведомление для {self.user_to}"

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('INSERT', 'Добавление'),
        ('UPDATE', 'Изменение'),
        ('DELETE', 'Удаление'),
    ]
    
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, verbose_name="Пользователь")
    action_time = models.DateTimeField(auto_now_add=True, verbose_name="Время действия")
    table_name = models.CharField(max_length=50, verbose_name="Таблица")
    record_id = models.IntegerField(verbose_name="ID записи")
    action_type = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name="Тип действия")
    old_data = models.JSONField(verbose_name="Старые данные", blank=True, null=True)
    new_data = models.JSONField(verbose_name="Новые данные", blank=True, null=True)
    ip_address = models.CharField(max_length=15, verbose_name="IP адрес", blank=True, null=True)
    user_agent = models.TextField(verbose_name="User Agent", blank=True, null=True)
    
    class Meta:
        verbose_name = "Лог аудита"
        verbose_name_plural = "Логи аудита"
        ordering = ['-action_time']
    
    def __str__(self):
        return f"{self.get_action_type_display()} в {self.table_name}"