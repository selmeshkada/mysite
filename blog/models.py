from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.urls import reverse

 
class UserManager(BaseUserManager):
    """Менеджер для кастомной модели пользователя"""
    def create_user(self, email, full_name, password=None, **extra_fields):
        """Создание обычного пользователя"""
        if not email:
            raise ValueError('Email должен быть указан')
        if not full_name:
            raise ValueError('Полное имя должно быть указано')
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            full_name=full_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email, full_name, password=None, **extra_fields):
        """Создание суперпользователя"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(email, full_name, password, **extra_fields)


class User(AbstractUser):
    """
    Модель пользователя (соответствует таблице users)
    """
    username = None
    first_name = None
    last_name = None
    
    email = models.EmailField(
        unique=True,
        verbose_name="Электронная почта"
    )
    full_name = models.CharField(
        max_length=255,
        verbose_name="Полное имя"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Телефон"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания"
    )

    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name="Аватар"
    )

    following = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='followers',
        verbose_name="Подписки"
    )

    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'users'
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email

User = get_user_model()

class CompanyMembership(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Владелец'),
        ('manager', 'Менеджер'),
        ('employee', 'Сотрудник'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_memberships', verbose_name= 'Пользователь')
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee', verbose_name= 'Роль')
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name= 'Дата присоединения')

    class Meta:
        unique_together = ['user', 'company']
        verbose_name = "Участник компании"
        verbose_name_plural = "Участники компаний"

    def __str__(self):
        return f"{self.user.full_name} - {self.company.name} ({self.get_role_display()})"


class SubscriptionPlan(models.Model):
    """
    Модель тарифных планов (subscription_plans)
    """
    name = models.CharField(
        max_length=100,
        verbose_name="Название тарифа"
    )
    price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена в месяц"
    )
    price_yearly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена в год"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )
    features = models.TextField(
        blank=True,
        help_text="Возможности тарифа, разделенные запятыми",
        verbose_name="Возможности"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания"
    )

    class Meta:
        db_table = 'subscription_plans'
        verbose_name = "Тарифный план"
        verbose_name_plural = "Тарифные планы"

    def __str__(self):
        return self.name

    def get_features_list(self):
        """Возвращает список возможностей"""
        return [f.strip() for f in self.features.split(',') if f.strip()]


class Subscription(models.Model):
    """
    Модель подписок пользователей (subscriptions)
    """
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('expired', 'Истекла'),
        ('cancelled', 'Отменена'),
        ('trial', 'Пробный период'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name="Пользователь"
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name="Тариф"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='trial',
        verbose_name="Статус"
    )
    start_date = models.DateField(
        verbose_name="Дата начала"
    )
    end_date = models.DateField(
        verbose_name="Дата окончания"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания"
    )

    class Meta:
        db_table = 'subscriptions'
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"


class Company(models.Model):
    """
    Модель компании (companies)
    """
    TAX_SYSTEM_CHOICES = [
        ('osn', 'ОСН'),
        ('usn_income', 'УСН (Доходы)'),
        ('usn_income_expense', 'УСН (Доходы минус расходы)'),
        ('eshn', 'ЕСХН'),
        ('patent', 'Патент'),
        ('npd', 'НПД'),
    ]

    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_companies',
        verbose_name="Создатель"
    )

    members = models.ManyToManyField(
        User,
        through='CompanyMembership',
        related_name='companies',
        verbose_name="Участники"
    )

    responsible_editor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='edited_companies',
        verbose_name="Ответственный за редактирование"
    )

    last_edited_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата последнего редактирования"
    )

    name = models.CharField(
        max_length=255,
        verbose_name="Название компании"
    )

    inn = models.CharField(
        max_length=12,
        verbose_name="ИНН"
    )

    ogrn = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="ОГРН"
    )
    legal_address = models.TextField(
        verbose_name="Юридический адрес"
    )
    tax_system = models.CharField(
        max_length=50,
        choices=TAX_SYSTEM_CHOICES,
        verbose_name="Система налогообложения"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания"
    )

    def is_incomplete(self):
        """Проверка, заполнены ли обязательные данные"""
        missing = []
        if not self.inn:
            missing.append('ИНН')
        if not self.legal_address:
            missing.append('Юридический адрес')
        return missing

    def save(self, *args, **kwargs):
        if not self.responsible_editor_id and self.creator_id:
            self.responsible_editor = self.creator
        super().save(*args, **kwargs)
        if self.is_incomplete() and self.responsible_editor:
            Notification.objects.create(
                user=self.responsible_editor,
                title=f"Неполные данные компании {self.name}",
                content=f"Отсутствуют поля: {', '.join(self.is_incomplete())}. Пожалуйста, заполните.",
                notification_date=timezone.now()
            )

    class Meta:
        db_table = 'companies'
        verbose_name = "Компания"
        verbose_name_plural = "Компании"

    def __str__(self):
        return f"{self.name} (ИНН: {self.inn})"
    
    
class Category(models.Model):
    CATEGORY_TYPE_CHOICES = [
        ('income', 'Доход'),
        ('expense', 'Расход'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='categories',
        verbose_name="Пользователь",
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100, verbose_name="Название категории")
    category_type = models.CharField(
        max_length=10, 
        choices=CATEGORY_TYPE_CHOICES,
        verbose_name="Тип категории"
    )
    color = models.CharField(
        max_length=7, 
        default='#0066cc',
        verbose_name="Цвет"
    )
    icon = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        verbose_name="Иконка"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    class Meta:
        unique_together = ['user', 'name', 'category_type']
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
    
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"
    
    def get_absolute_url(self):
        return reverse('blog:category-list')
    
    
class Transaction(models.Model):
    """
    Модель транзакций (transactions)
    """
    OPERATION_TYPE_CHOICES = [
        ('income', 'Доход'),
        ('expense', 'Расход'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="Компания"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions',
        verbose_name="Категория"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Сумма"
    )
    operation_type = models.CharField(
        max_length=10,
        choices=OPERATION_TYPE_CHOICES,
        verbose_name="Тип операции"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание"
    )
    counterparty = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Контрагент"
    )
    transaction_date = models.DateField(
        verbose_name="Дата операции"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания"
    )

    class Meta:
        db_table = 'transactions'
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return f"{self.transaction_date} | {self.company.name} | {self.amount} ₽"


class Report(models.Model):
    """
    Модель отчетов (reports)
    """
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('generating', 'Генерируется'),
        ('ready', 'Готов'),
        ('error', 'Ошибка'),
    ]

    REPORT_TYPE_CHOICES = [
        ('profit_loss', 'Прибыли и убытки'),
        ('balance', 'Баланс'),
        ('tax', 'Налоговый отчет'),
        ('custom', 'Пользовательский'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name="Компания"
    )
    report_type = models.CharField(
        max_length=50,
        choices=REPORT_TYPE_CHOICES,
        verbose_name="Тип отчета"
    )
    period_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name="Месяц"
    )
    period_year = models.IntegerField(
        verbose_name="Год"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Статус"
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Путь к файлу"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания"
    )

    class Meta:
        db_table = 'reports'
        verbose_name = "Отчет"
        verbose_name_plural = "Отчеты"
        ordering = ['-period_year', '-period_month']

    def __str__(self):
        return f"{self.company.name} - {self.get_report_type_display()} {self.period_month}.{self.period_year}"


class Notification(models.Model):
    """
    Модель уведомлений (notifications)
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Пользователь"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Заголовок"
    )
    content = models.TextField(
        verbose_name="Содержание"
    )
    notification_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата уведомления"
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name="Прочитано"
    )

    class Meta:
        db_table = 'notifications'
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-notification_date']

    def __str__(self):
        return f"{self.user.email} - {self.title}"
    