from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from .models import User, Organization, AuditorCompany, Application, Document, Notification
from .forms import ApplicationForm, DocumentForm 
from django.db.models import Count, Q
from django.contrib import messages


def home(request):
    context = {
        'organizations_count': Organization.objects.count(),
        'auditors_count': AuditorCompany.objects.count(),
        'applications_count': Application.objects.count(),
        'latest_applications': Application.objects.order_by('-date')[:5],
        'top_auditors': AuditorCompany.objects.annotate(
            completed_count=Count('applications', filter=Q(applications__status='Завершено'))
        ).order_by('-completed_count')[:5],
        'user_notifications': Notification.objects.filter(user_to=request.user).order_by('-sent_date')[:5] if request.user.is_authenticated else None
    }
    return render(request, 'blog/home.html', context)

class ApplicationListView(LoginRequiredMixin, ListView):
    model = Application
    template_name = 'blog/application_list.html'
    context_object_name = 'applications'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.role == 'Организация':
            return Application.objects.filter(organization__user=self.request.user)
        elif self.request.user.role == 'Аудитор':
            return Application.objects.filter(auditor_company__user=self.request.user)
        return Application.objects.none()
    def application_list(request):
        applications = Application.objects.all().order_by('-date') 
        return render(request, 'application_table.html', {'applications': applications})


class ApplicationDetailView(LoginRequiredMixin, DetailView):
    model = Application
    template_name = 'blog/application_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = Document.objects.filter(application=self.object)
        return context


class ApplicationCreateView(LoginRequiredMixin, CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'blog/application_form.html'

    def form_valid(self, form):
        form.instance.organization = get_object_or_404(Organization, user=self.request.user)
        return super().form_valid(form)

class ApplicationUpdateView(LoginRequiredMixin, UpdateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'blog/application_form.html'

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
    return render(request, 'blog/document_upload.html', {'form': form, 'application': application})

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'blog/notification_list.html'
    context_object_name = 'notifications'

    def get_queryset(self):
        return Notification.objects.filter(user_to=self.request.user).order_by('-sent_date')
    
@login_required
def mark_notification_read(request, pk):
    """Пометить одно уведомление как прочитанное"""
    notification = get_object_or_404(Notification, id=pk, user_to=request.user)  # user_to - поле в модели Notification
    notification.is_read = True
    notification.save()
    return redirect('notification-list')

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
    
    return render(request, 'blog/profile.html', context)

class AuditorListView(ListView):
    model = AuditorCompany
    template_name = 'blog/auditor_list.html'
    context_object_name = 'auditors'
    paginate_by = 10

    def get_queryset(self):
        return AuditorCompany.objects.annotate(
            completed_count=Count(
                'applications',
                filter=Q(applications__status='Завершено')
        ).order_by('-completed_count'))