from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from .models import User, Organization, AuditorCompany, Application, Document, Notification
from .forms import ApplicationForm, DocumentForm  # Эти формы нужно создать

# Главная страница (замените на свою логику)
def home(request):
    context = {
        'applications_count': Application.objects.count(),
        'organizations_count': Organization.objects.count(),
        'auditors_count': AuditorCompany.objects.count()
    }
    return render(request, 'mysite\blog\templates\blog\home.html', context)

# Список заявок
class ApplicationListView(LoginRequiredMixin, ListView):
    model = Application
    template_name = 'blog/templates/blog/application_list.html'
    context_object_name = 'applications'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.role == 'Организация':
            return Application.objects.filter(organization__user=user)
        elif user.role == 'Аудитор':
            return Application.objects.filter(auditor_company__user=user)
        return Application.objects.all()

# Детали заявки
class ApplicationDetailView(LoginRequiredMixin, DetailView):
    model = Application
    template_name = 'blog/templates/blog/application_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = Document.objects.filter(application=self.object)
        return context

# Создание новой заявки
class ApplicationCreateView(LoginRequiredMixin, CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'blog/templates/blog/application_form.html'

    def form_valid(self, form):
        form.instance.organization = get_object_or_404(Organization, user=self.request.user)
        return super().form_valid(form)

# Редактирование заявки
class ApplicationUpdateView(LoginRequiredMixin, UpdateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'blog/templates/blog/application_form.html'

# Загрузка документа к заявке
@login_required
def upload_document(request, app_id):
    application = get_object_or_404(Application, pk=app_id)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.application = application
            document.uploaded_by = request.user
            document.save()
            return redirect('application-detail', pk=app_id)
    else:
        form = DocumentForm()
    return render(request, 'blog/templates/blog/document_upload.html', {'form': form, 'application': application})

# Уведомления пользователя
class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'blog/templates/blog/notification_list.html'
    context_object_name = 'notifications'

    def get_queryset(self):
        return Notification.objects.filter(user_to=self.request.user).order_by('-sent_date')

# Пометить уведомление как прочитанное
@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user_to=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notification-list')

# Профиль пользователя
@login_required
def profile(request):
    user = request.user
    context = {'user': user}
    
    if user.role == 'Организация':
        context['organization'] = get_object_or_404(Organization, user=user)
        context['applications'] = Application.objects.filter(organization__user=user)[:5]
    elif user.role == 'Аудитор':
        context['auditor_company'] = get_object_or_404(AuditorCompany, user=user)
        context['applications'] = Application.objects.filter(auditor_company__user=user)[:5]
    
    return render(request, 'blog/templates/blog/profile.html', context)