from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from .models import User, Organization, AuditorCompany, Application, Document, Notification
from .forms import ApplicationForm, DocumentForm 
from django.db.models import Count, Q, Avg, Case, When, FloatField
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import DeleteView
from django.urls import reverse_lazy

def home(request):
    completed_percentage = Application.objects.aggregate(
        avg_completed=Avg(
            Case(
                When(status='Завершено', then=100),
                default=0,
                output_field=FloatField()
            )
        )
    )['avg_completed'] or 0

    context = {
        'organizations_count': Organization.objects.count(),
        'auditors_count': AuditorCompany.objects.count(),
        'applications_count': Application.objects.count(),
        'completed_percentage': round(completed_percentage, 1),
        'latest_applications': Application.objects.select_related(
            'organization', 'auditor_company'
            ).order_by('-date')[:10],
        'top_auditors': AuditorCompany.objects.annotate(
            completed_count=Count('applications', filter=Q(applications__status='Завершено'))
        ).filter(completed_count__gt=0).order_by('-completed_count')[:10],
        'user_notifications': Notification.objects.filter(user_to=request.user).order_by('-sent_date')[:10] if request.user.is_authenticated else None
    }
    return render(request, 'blog/home.html', context)

class ApplicationListView(LoginRequiredMixin, ListView):
    template_name = 'blog/application_list.html'
    context_object_name = 'applications'
    paginate_by = 10

    def get_queryset(self):
        queryset = Application.objects.select_related('organization', 'auditor_company').order_by('-date')
        
        if self.request.user.role == 'Организация':
            queryset = queryset.filter(organization__user=self.request.user)
        elif self.request.user.role == 'Аудитор':
            queryset = queryset.filter(auditor_company__user=self.request.user)
        elif self.request.user.role != 'Администратор':
            queryset = Application.objects.none()
        
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(organization__name__icontains=query) |
                Q(auditor_company__name__icontains=query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class ApplicationDetailView(LoginRequiredMixin, DetailView):
    model = Application
    template_name = 'blog/application_detail.html'
    success_url = reverse_lazy('blog:application-list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = Document.objects.filter(application=self.object)
        return context


class ApplicationCreateView(LoginRequiredMixin, CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'blog/application_form.html'
    success_url = reverse_lazy('blog:application-list')

    def form_valid(self, form):
        form.instance.organization = get_object_or_404(Organization, user=self.request.user)
        return super().form_valid(form)

class ApplicationUpdateView(LoginRequiredMixin, UpdateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'blog/application_form.html'
    success_url = reverse_lazy('blog:application-list')

    
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
    notification = get_object_or_404(Notification, id=pk, user_to=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'notification_id': pk})
    return redirect('blog:notification-list')

@login_required
def profile(request):
    user = request.user
    context = {'user': user}
    
    if user.role == 'Организация':
        context['organization'] = get_object_or_404(Organization, user=user)
        context['applications'] = Application.objects.filter(organization__user=user)[:10]
    elif user.role == 'Аудитор':
        context['auditor_company'] = get_object_or_404(AuditorCompany, user=user)
        context['applications'] = Application.objects.filter(auditor_company__user=user)[:10]
    
    return render(request, 'blog/profile.html', context)

class AuditorListView(ListView):
    model = AuditorCompany
    template_name = 'blog/auditor_list.html'
    context_object_name = 'auditors'
    paginate_by = 10

    def get_queryset(self):
        queryset = AuditorCompany.objects.annotate(
            completed_count=Count(
                'applications',
                filter=Q(applications__status='Завершено')
            )
        )
        return queryset.order_by('-completed_count')
    
class ApplicationSearchView(LoginRequiredMixin, ListView):
    template_name = 'blog/application_list.html'
    context_object_name = 'applications'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        base_queryset = Application.objects.select_related('organization', 'auditor_company').order_by('-date')
        
        if query:
            return base_queryset.filter(
                Q(organization__name__icontains=query) |
                Q(auditor_company__name__icontains=query)
            )
        
        return base_queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context

class ApplicationDeleteView(LoginRequiredMixin, DeleteView):
    model = Application
    template_name = 'blog/application_confirm_delete.html'
    success_url = reverse_lazy('blog:application-list')

    def dispatch(self, request, *args, **kwargs):
            app = self.get_object()
            # Только владелец может удалить
            if request.user != app.organization.user and request.user.role != 'Администратор':
                return redirect('blog:application-list')
            return super().dispatch(request, *args, **kwargs)