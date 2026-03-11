from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum, Count, Avg
from django.db.models.functions import TruncMonth, TruncYear
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout

from .models import (
    User, SubscriptionPlan, Subscription, Company,
    Category, Transaction, Report, Notification
)
from .forms import (
    UserRegistrationForm, UserLoginForm, UserProfileForm,
    SubscriptionPlanForm, SubscriptionForm, CompanyForm,
    CategoryForm, TransactionForm, ReportForm, ReportGenerateForm,
    TransactionFilterForm, ReportFilterForm, NotificationForm
)


# ============== СТРАНИЦЫ САЙТА (PUBLIC) ==============

def landing_page(request):
    """Главная страница (лендинг)"""
    plans = SubscriptionPlan.objects.filter(is_active=True)[:3]
    context = {
        'plans': plans,
    }
    return render(request, 'blog/landing.html', context)


def reg_page(request):
    """Страница регистрации"""
    if request.user.is_authenticated:
        return redirect('blog:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Автоматический вход после регистрации
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать!')
            return redirect('blog:dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'blog/reg.html', {'form': form})


def login_page(request):
    """Страница входа"""
    if request.user.is_authenticated:
        return redirect('blog:dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user)
                
                # Запоминаем пользователя если стоит галочка
                if not form.cleaned_data.get('remember_me'):
                    request.session.set_expiry(0)
                
                messages.success(request, f'С возвращением, {user.full_name}!')
                return redirect('blog:dashboard')
            else:
                messages.error(request, 'Неверный email или пароль')
    else:
        form = UserLoginForm()
    
    return render(request, 'blog/login.html', {'form': form})


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('blog:landing')


# ============== ЛИЧНЫЙ КАБИНЕТ ==============

@login_required
def dashboard_page(request):
    """Дашборд (личный кабинет)"""
    user = request.user
    
    # Получаем компании пользователя
    companies = Company.objects.filter(creator=user)
    
    # Получаем текущую подписку
    current_subscription = Subscription.objects.filter(
        user=user,
        status__in=['active', 'trial']
    ).first()
    
    # Статистика за текущий месяц
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # Доходы и расходы по всем компаниям
    monthly_income = Transaction.objects.filter(
        company__in=companies,
        operation_type='income',
        transaction_date__gte=month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    monthly_expense = Transaction.objects.filter(
        company__in=companies,
        operation_type='expense',
        transaction_date__gte=month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Последние операции
    recent_transactions = Transaction.objects.filter(
        company__in=companies
    ).select_related('company', 'category').order_by('-transaction_date')[:10]
    
    # Активные уведомления
    unread_notifications = Notification.objects.filter(
        user=user,
        is_read=False
    ).order_by('-notification_date')[:5]
    
    context = {
        'companies': companies,
        'current_subscription': current_subscription,
        'monthly_income': monthly_income,
        'monthly_expense': monthly_expense,
        'balance': monthly_income - monthly_expense,
        'recent_transactions': recent_transactions,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'blog/dashboard.html', context)


@login_required
def finance_page(request):
    """Страница финансов и операций"""
    return render(request, 'blog/finance.html')


@login_required
def reports_page(request):
    """Страница отчетности"""
    return render(request, 'blog/reports.html')


# ============== API ДЛЯ ДАШБОРДА ==============

@login_required
def dashboard_data(request):
    """API для получения данных дашборда (AJAX)"""
    user = request.user
    companies = Company.objects.filter(creator=user)
    
    # Период по умолчанию - последние 30 дней
    days = int(request.GET.get('days', 30))
    date_from = timezone.now().date() - timedelta(days=days)
    
    # Динамика по дням
    daily_stats = Transaction.objects.filter(
        company__in=companies,
        transaction_date__gte=date_from
    ).values('transaction_date', 'operation_type').annotate(
        total=Sum('amount')
    ).order_by('transaction_date')
    
    # Статистика по категориям
    category_stats = Transaction.objects.filter(
        company__in=companies,
        transaction_date__gte=date_from,
        operation_type='expense'
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Баланс по компаниям (доходы - расходы)
    company_balance = []
    for company in companies:
        income = Transaction.objects.filter(
            company=company,
            operation_type='income'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expense = Transaction.objects.filter(
            company=company,
            operation_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        company_balance.append({
            'id': company.id,
            'name': company.name,
            'balance': income - expense,
            'income': income,
            'expense': expense,
        })
    
    context = {
        'daily_stats': list(daily_stats),
        'category_stats': list(category_stats),
        'company_balance': company_balance,
    }
    return JsonResponse(context)


# ============== УПРАВЛЕНИЕ КОМПАНИЯМИ ==============

class CompanyListView(LoginRequiredMixin, ListView):
    """Список компаний пользователя"""
    model = Company
    template_name = 'blog/company_list.html'
    context_object_name = 'companies'

    def get_queryset(self):
        return Company.objects.filter(creator=self.request.user)


class CompanyDetailView(LoginRequiredMixin, DetailView):
    """Детали компании"""
    model = Company
    template_name = 'blog/company_detail.html'

    def get_queryset(self):
        return Company.objects.filter(creator=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transactions'] = Transaction.objects.filter(
            company=self.object
        ).select_related('category').order_by('-transaction_date')[:20]
        context['reports'] = Report.objects.filter(
            company=self.object
        ).order_by('-period_year', '-period_month')[:10]
        return context


class CompanyCreateView(LoginRequiredMixin, CreateView):
    """Создание новой компании"""
    model = Company
    form_class = CompanyForm
    template_name = 'blog/company_form.html'
    success_url = reverse_lazy('blog:company-list')

    def form_valid(self, form):
        form.instance.creator = self.request.user
        messages.success(self.request, 'Компания успешно создана')
        return super().form_valid(form)


class CompanyUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование компании"""
    model = Company
    form_class = CompanyForm
    template_name = 'blog/company_form.html'

    def get_queryset(self):
        return Company.objects.filter(creator=self.request.user)

    def get_success_url(self):
        messages.success(self.request, 'Компания успешно обновлена')
        return reverse('blog:company-detail', kwargs={'pk': self.object.pk})


class CompanyDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление компании"""
    model = Company
    template_name = 'blog/company_confirm_delete.html'
    success_url = reverse_lazy('blog:company-list')

    def get_queryset(self):
        return Company.objects.filter(creator=self.request.user)

    def delete(self, request, *args, **kwargs):
        # Проверяем, есть ли транзакции
        if Transaction.objects.filter(company=self.get_object()).exists():
            messages.error(request, 'Нельзя удалить компанию, в которой есть операции')
            return redirect('blog:company-list')
        
        messages.success(request, 'Компания успешно удалена')
        return super().delete(request, *args, **kwargs)


# ============== УПРАВЛЕНИЕ КАТЕГОРИЯМИ ==============

class CategoryListView(LoginRequiredMixin, ListView):
    """Список категорий"""
    model = Category
    template_name = 'blog/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def get_queryset(self):
        return Category.objects.all().order_by('type', 'name')


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Создание новой категории"""
    model = Category
    form_class = CategoryForm
    template_name = 'blog/category_form.html'
    success_url = reverse_lazy('blog:category-list')

    def form_valid(self, form):
        messages.success(self.request, 'Категория успешно создана')
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование категории"""
    model = Category
    form_class = CategoryForm
    template_name = 'blog/category_form.html'

    def get_success_url(self):
        messages.success(self.request, 'Категория успешно обновлена')
        return reverse('blog:category-list')


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление категории"""
    model = Category
    template_name = 'blog/category_confirm_delete.html'
    success_url = reverse_lazy('blog:category-list')

    def delete(self, request, *args, **kwargs):
        # Проверяем, есть ли транзакции с этой категорией
        if Transaction.objects.filter(category=self.get_object()).exists():
            messages.error(request, 'Нельзя удалить категорию, в которой есть операции')
            return redirect('blog:category-list')
        
        messages.success(request, 'Категория успешно удалена')
        return super().delete(request, *args, **kwargs)


# ============== УПРАВЛЕНИЕ ТРАНЗАКЦИЯМИ ==============

class TransactionListView(LoginRequiredMixin, ListView):
    """Список транзакций с фильтрацией"""
    model = Transaction
    template_name = 'blog/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 20

    def get_queryset(self):
        companies = Company.objects.filter(creator=self.request.user)
        queryset = Transaction.objects.filter(
            company__in=companies
        ).select_related('company', 'category').order_by('-transaction_date', '-created_at')
        
        # Применяем фильтры из формы
        form = TransactionFilterForm(self.request.GET, user=self.request.user)
        if form.is_valid():
            data = form.cleaned_data
            
            if data.get('date_from'):
                queryset = queryset.filter(transaction_date__gte=data['date_from'])
            
            if data.get('date_to'):
                queryset = queryset.filter(transaction_date__lte=data['date_to'])
            
            if data.get('operation_type'):
                queryset = queryset.filter(operation_type=data['operation_type'])
            
            if data.get('category'):
                queryset = queryset.filter(category=data['category'])
            
            if data.get('company'):
                queryset = queryset.filter(company=data['company'])
            
            if data.get('min_amount'):
                queryset = queryset.filter(amount__gte=data['min_amount'])
            
            if data.get('max_amount'):
                queryset = queryset.filter(amount__lte=data['max_amount'])
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = TransactionFilterForm(
            self.request.GET,
            user=self.request.user
        )
        return context


class TransactionDetailView(LoginRequiredMixin, DetailView):
    """Детали транзакции"""
    model = Transaction
    template_name = 'blog/transaction_detail.html'

    def get_queryset(self):
        companies = Company.objects.filter(creator=self.request.user)
        return Transaction.objects.filter(company__in=companies)


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Создание новой транзакции"""
    model = Transaction
    form_class = TransactionForm
    template_name = 'blog/transaction_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Операция успешно добавлена')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:transaction-detail', kwargs={'pk': self.object.pk})


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование транзакции"""
    model = Transaction
    form_class = TransactionForm
    template_name = 'blog/transaction_form.html'

    def get_queryset(self):
        companies = Company.objects.filter(creator=self.request.user)
        return Transaction.objects.filter(company__in=companies)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Операция успешно обновлена')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:transaction-detail', kwargs={'pk': self.object.pk})


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление транзакции"""
    model = Transaction
    template_name = 'blog/transaction_confirm_delete.html'
    success_url = reverse_lazy('blog:transaction-list')

    def get_queryset(self):
        companies = Company.objects.filter(creator=self.request.user)
        return Transaction.objects.filter(company__in=companies)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Операция успешно удалена')
        return super().delete(request, *args, **kwargs)


# ============== УПРАВЛЕНИЕ ОТЧЕТАМИ ==============

class ReportListView(LoginRequiredMixin, ListView):
    """Список отчетов"""
    model = Report
    template_name = 'blog/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20

    def get_queryset(self):
        companies = Company.objects.filter(creator=self.request.user)
        queryset = Report.objects.filter(
            company__in=companies
        ).select_related('company').order_by('-period_year', '-period_month')
        
        # Применяем фильтры
        form = ReportFilterForm(self.request.GET, user=self.request.user)
        if form.is_valid():
            data = form.cleaned_data
            
            if data.get('company'):
                queryset = queryset.filter(company=data['company'])
            
            if data.get('report_type'):
                queryset = queryset.filter(report_type=data['report_type'])
            
            if data.get('status'):
                queryset = queryset.filter(status=data['status'])
            
            if data.get('year'):
                queryset = queryset.filter(period_year=data['year'])
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ReportFilterForm(
            self.request.GET,
            user=self.request.user
        )
        return context


class ReportCreateView(LoginRequiredMixin, CreateView):
    """Создание нового отчета"""
    model = Report
    form_class = ReportForm
    template_name = 'blog/report_form.html'
    success_url = reverse_lazy('blog:report-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Отчет успешно создан')
        return super().form_valid(form)


class ReportDetailView(LoginRequiredMixin, DetailView):
    """Детали отчета"""
    model = Report
    template_name = 'blog/report_detail.html'

    def get_queryset(self):
        companies = Company.objects.filter(creator=self.request.user)
        return Report.objects.filter(company__in=companies)


class ReportDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление отчета"""
    model = Report
    template_name = 'blog/report_confirm_delete.html'
    success_url = reverse_lazy('blog:report-list')

    def get_queryset(self):
        companies = Company.objects.filter(creator=self.request.user)
        return Report.objects.filter(company__in=companies)


@login_required
def generate_report(request):
    """Генерация отчета за период"""
    if request.method == 'POST':
        form = ReportGenerateForm(request.POST, user=request.user)
        if form.is_valid():
            data = form.cleaned_data
            company = data['company']
            report_type = data['report_type']
            date_from = data['date_from']
            date_to = data['date_to']
            file_format = data['format']
            
            # Здесь будет логика генерации отчета
            # Создание записи в БД и генерация файла
            
            messages.success(request, 'Отчет генерируется. Вы получите уведомление о готовности.')
            return redirect('blog:report-list')
    else:
        form = ReportGenerateForm(user=request.user)
    
    return render(request, 'blog/generate_report.html', {'form': form})


# ============== УПРАВЛЕНИЕ ПОДПИСКАМИ ==============

class SubscriptionPlanListView(ListView):
    """Список доступных тарифов"""
    model = SubscriptionPlan
    template_name = 'blog/plan_list.html'
    context_object_name = 'plans'

    def get_queryset(self):
        return SubscriptionPlan.objects.filter(is_active=True)


class SubscriptionPlanDetailView(DetailView):
    """Детали тарифа"""
    model = SubscriptionPlan
    template_name = 'blog/plan_detail.html'

    def get_queryset(self):
        return SubscriptionPlan.objects.filter(is_active=True)


@login_required
def subscribe(request, plan_id):
    """Оформление подписки на тариф"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    
    if request.method == 'POST':
        form = SubscriptionForm(request.POST, user=request.user)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.user = request.user
            subscription.plan = plan
            subscription.save()
            
            messages.success(request, f'Подписка на тариф "{plan.name}" оформлена!')
            return redirect('blog:dashboard')
    else:
        initial = {
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timedelta(days=30),
            'status': 'trial' if not request.user.subscriptions.exists() else 'active'
        }
        form = SubscriptionForm(initial=initial, user=request.user)
    
    return render(request, 'blog/subscription_form.html', {
        'form': form,
        'plan': plan
    })


class UserSubscriptionListView(LoginRequiredMixin, ListView):
    """Список подписок пользователя"""
    model = Subscription
    template_name = 'blog/user_subscriptions.html'
    context_object_name = 'subscriptions'

    def get_queryset(self):
        return Subscription.objects.filter(
            user=self.request.user
        ).select_related('plan').order_by('-created_at')


# ============== УПРАВЛЕНИЕ УВЕДОМЛЕНИЯМИ ==============

class NotificationListView(LoginRequiredMixin, ListView):
    """Список уведомлений"""
    model = Notification
    template_name = 'blog/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-notification_date')


@login_required
def mark_notification_read(request, pk):
    """Отметить уведомление как прочитанное"""
    notification = get_object_or_404(Notification, id=pk, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'notification_id': pk})
    
    return redirect('blog:notification-list')


@login_required
def mark_all_notifications_read(request):
    """Отметить все уведомления как прочитанные"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'Все уведомления отмечены как прочитанные')
    return redirect('blog:notification-list')


# ============== ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ==============

@login_required
def profile_view(request):
    """Профиль пользователя"""
    user = request.user
    
    # Статистика
    companies_count = Company.objects.filter(creator=user).count()
    transactions_count = Transaction.objects.filter(
        company__in=Company.objects.filter(creator=user)
    ).count()
    
    # Текущая подписка
    current_subscription = Subscription.objects.filter(
        user=user,
        status__in=['active', 'trial']
    ).first()
    
    context = {
        'user': user,
        'companies_count': companies_count,
        'transactions_count': transactions_count,
        'current_subscription': current_subscription,
    }
    return render(request, 'blog/profile.html', context)


@login_required
def profile_edit(request):
    """Редактирование профиля"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен')
            return redirect('blog:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'blog/profile_edit.html', {'form': form})
