from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .models import (User, SubscriptionPlan, Subscription, Company, Category, Transaction, Report, Notification)
from .models import User
from django.contrib.auth import authenticate

class UserRegistrationForm(forms.ModelForm):
    full_name = forms.CharField(
        label='Полное имя',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Иван Иванов'})
    )

    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-input'})
    )

    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-input'})
    )

    password2 = forms.CharField(
        label='Повторите пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-input'})
    )

    class Meta:
        model = User
        fields = ['full_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь уже существует')
        return email

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('password2'):
            raise forms.ValidationError('Пароли не совпадают')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class DateInput(forms.DateInput):
    """Кастомный виджет для выбора даты"""
    input_type = 'date'


class DateTimeInput(forms.DateTimeInput):
    """Кастомный виджет для выбора даты и времени"""
    input_type = 'datetime-local'



class UserLoginForm(forms.Form):
    """Форма входа пользователя"""
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'example@mail.ru'
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите пароль'
        })
    )
    remember_me = forms.BooleanField(
        label='Запомнить меня',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )


# ============== ФОРМЫ ДЛЯ ТАРИФОВ ==============

class SubscriptionPlanForm(forms.ModelForm):
    """Форма для создания/редактирования тарифного плана"""
    class Meta:
        model = SubscriptionPlan
        fields = ['name', 'price_monthly', 'price_yearly', 'description', 'features', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Базовый'
            }),
            'price_monthly': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '500.00',
                'step': '0.01',
                'min': '0'
            }),
            'price_yearly': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '5000.00',
                'step': '0.01',
                'min': '0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Описание тарифа',
                'rows': 4
            }),
            'features': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Введите возможности через запятую (например: учет доходов, отчеты, аналитика)',
                'rows': 3
            }),
        }
        labels = {
            'name': 'Название тарифа',
            'price_monthly': 'Цена в месяц (₽)',
            'price_yearly': 'Цена в год (₽)',
            'description': 'Описание',
            'features': 'Возможности',
            'is_active': 'Активен',
        }


class SubscriptionForm(forms.ModelForm):
    """Форма для оформления подписки"""
    class Meta:
        model = Subscription
        fields = ['plan', 'start_date', 'end_date', 'status']
        widgets = {
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'start_date': DateInput(attrs={'class': 'form-input'}),
            'end_date': DateInput(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'plan': 'Тарифный план',
            'start_date': 'Дата начала',
            'end_date': 'Дата окончания',
            'status': 'Статус',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['plan'].queryset = SubscriptionPlan.objects.filter(is_active=True)

    def clean(self):
        """Валидация дат"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('Дата окончания должна быть позже даты начала')

        return cleaned_data


# ============== ФОРМЫ ДЛЯ КОМПАНИЙ ==============

class CompanyForm(forms.ModelForm):
    """Форма для создания/редактирования компании"""
    class Meta:
        model = Company
        fields = ['name', 'inn', 'ogrn', 'legal_address', 'tax_system']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'ООО "Ромашка"'
            }),
            'inn': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '1234567890'
            }),
            'ogrn': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '1234567890123'
            }),
            'legal_address': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'г. Москва, ул. Пушкина, д. 10',
                'rows': 3
            }),
            'tax_system': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'name': 'Название компании',
            'inn': 'ИНН',
            'ogrn': 'ОГРН',
            'legal_address': 'Юридический адрес',
            'tax_system': 'Система налогообложения',
        }

    def clean_inn(self):
        """Валидация ИНН"""
        inn = self.cleaned_data.get('inn')
        if inn and not inn.isdigit():
            raise forms.ValidationError('ИНН должен содержать только цифры')
        if inn and len(inn) not in [10, 12]:
            raise forms.ValidationError('ИНН должен содержать 10 или 12 цифр')
        return inn

    def clean_ogrn(self):
        """Валидация ОГРН"""
        ogrn = self.cleaned_data.get('ogrn')
        if ogrn and not ogrn.isdigit():
            raise forms.ValidationError('ОГРН должен содержать только цифры')
        if ogrn and len(ogrn) not in [13, 15]:
            raise forms.ValidationError('ОГРН должен содержать 13 или 15 цифр')
        return ogrn


# ============== ФОРМЫ ДЛЯ КАТЕГОРИЙ ==============

class CategoryForm(forms.ModelForm):
    """Форма для создания/редактирования категории"""
    class Meta:
        model = Category
        fields = ['name', 'type', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Продукты'
            }),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'icon': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'shopping-cart'
            }),
        }
        labels = {
            'name': 'Название категории',
            'type': 'Тип',
            'icon': 'Иконка',
        }

    def clean_name(self):
        """Валидация уникальности названия категории"""
        name = self.cleaned_data.get('name')
        category_type = self.cleaned_data.get('type')
        
        if name and category_type:
            existing = Category.objects.filter(
                name__iexact=name,
                type=category_type
            )
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(f'Категория "{name}" с таким типом уже существует')
        
        return name


# ============== ФОРМЫ ДЛЯ ТРАНЗАКЦИЙ ==============

class TransactionForm(forms.ModelForm):
    """Форма для создания/редактирования транзакции"""
    class Meta:
        model = Transaction
        fields = ['company', 'category', 'amount', 'operation_type', 
                  'description', 'counterparty', 'transaction_date']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'operation_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'operation-type'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Описание операции',
                'rows': 3
            }),
            'counterparty': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'ООО "Поставщик"'
            }),
            'transaction_date': DateInput(attrs={'class': 'form-input'}),
        }
        labels = {
            'company': 'Компания',
            'category': 'Категория',
            'amount': 'Сумма',
            'operation_type': 'Тип операции',
            'description': 'Описание',
            'counterparty': 'Контрагент',
            'transaction_date': 'Дата операции',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Фильтруем компании только текущего пользователя
            self.fields['company'].queryset = Company.objects.filter(creator=self.user)
            
            # Ограничиваем категории по типу (будут фильтроваться через JS)
            self.fields['category'].queryset = Category.objects.all()

    def clean_transaction_date(self):
        """Валидация даты (не в будущем)"""
        date = self.cleaned_data.get('transaction_date')
        if date and date > timezone.now().date():
            raise forms.ValidationError('Дата операции не может быть в будущем')
        return date

    def clean_amount(self):
        """Валидация суммы"""
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Сумма должна быть больше 0')
        return amount


# ============== ФОРМЫ ДЛЯ ОТЧЕТОВ ==============

class ReportForm(forms.ModelForm):
    """Форма для создания отчета"""
    class Meta:
        model = Report
        fields = ['company', 'report_type', 'period_month', 'period_year']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-select'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'period_month': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '1-12',
                'min': '1',
                'max': '12'
            }),
            'period_year': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '2026',
                'min': '2000',
                'max': '2100'
            }),
        }
        labels = {
            'company': 'Компания',
            'report_type': 'Тип отчета',
            'period_month': 'Месяц',
            'period_year': 'Год',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['company'].queryset = Company.objects.filter(creator=self.user)

    def clean(self):
        """Валидация месяца и года"""
        cleaned_data = super().clean()
        month = cleaned_data.get('period_month')
        year = cleaned_data.get('period_year')
        
        if month and (month < 1 or month > 12):
            raise forms.ValidationError('Месяц должен быть от 1 до 12')
        
        if year and year > timezone.now().year + 1:
            raise forms.ValidationError('Год не может быть больше следующего')
        
        return cleaned_data


class ReportGenerateForm(forms.Form):
    """Форма для генерации отчета за период"""
    company = forms.ModelChoiceField(
        label='Компания',
        queryset=Company.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    report_type = forms.ChoiceField(
        label='Тип отчета',
        choices=Report.REPORT_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        label='Дата с',
        widget=DateInput(attrs={'class': 'form-input'})
    )
    date_to = forms.DateField(
        label='Дата по',
        widget=DateInput(attrs={'class': 'form-input'})
    )
    format = forms.ChoiceField(
        label='Формат',
        choices=[('pdf', 'PDF'), ('excel', 'Excel'), ('csv', 'CSV')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['company'].queryset = Company.objects.filter(creator=user)

    def clean(self):
        """Валидация дат"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError('Дата "С" должна быть раньше даты "По"')
        
        if date_from and date_from > timezone.now().date():
            raise forms.ValidationError('Дата начала не может быть в будущем')
        
        return cleaned_data


# ============== ФОРМЫ ДЛЯ УВЕДОМЛЕНИЙ ==============

class NotificationForm(forms.ModelForm):
    """Форма для создания уведомления"""
    class Meta:
        model = Notification
        fields = ['title', 'content', 'notification_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Заголовок уведомления'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Текст уведомления',
                'rows': 4
            }),
            'notification_date': DateTimeInput(attrs={'class': 'form-input'}),
        }
        labels = {
            'title': 'Заголовок',
            'content': 'Содержание',
            'notification_date': 'Дата отправки',
        }


# ============== ФОРМЫ ДЛЯ ФИЛЬТРАЦИИ ==============

class TransactionFilterForm(forms.Form):
    """Форма для фильтрации транзакций"""
    date_from = forms.DateField(
        label='С',
        required=False,
        widget=DateInput(attrs={'class': 'form-input'})
    )
    date_to = forms.DateField(
        label='По',
        required=False,
        widget=DateInput(attrs={'class': 'form-input'})
    )
    operation_type = forms.ChoiceField(
        label='Тип операции',
        required=False,
        choices=[('', 'Все')] + Transaction.OPERATION_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        label='Категория',
        required=False,
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    company = forms.ModelChoiceField(
        label='Компания',
        required=False,
        queryset=Company.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    min_amount = forms.DecimalField(
        label='Сумма от',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': '0',
            'step': '0.01'
        })
    )
    max_amount = forms.DecimalField(
        label='Сумма до',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': '1000000',
            'step': '0.01'
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['company'].queryset = Company.objects.filter(creator=user)


class ReportFilterForm(forms.Form):
    """Форма для фильтрации отчетов"""
    company = forms.ModelChoiceField(
        label='Компания',
        required=False,
        queryset=Company.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    report_type = forms.ChoiceField(
        label='Тип отчета',
        required=False,
        choices=[('', 'Все')] + Report.REPORT_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        label='Статус',
        required=False,
        choices=[('', 'Все')] + Report.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    year = forms.IntegerField(
        label='Год',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': '2026',
            'min': '2000',
            'max': '2100'
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['company'].queryset = Company.objects.filter(creator=user)

            