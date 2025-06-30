from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import render, redirect
from .models import *
from .forms import *
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone 
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from datetime import date
from django.views.decorators.http import require_POST


def index(request):    
    service_categories = ServiceСategories.objects.filter(is_archived=False)

    services_by_category = {}
    for category in service_categories:
        services_by_category[category] = Service.objects.filter(service_categories=category, is_archived=False)
    
    doctors = Doctors.objects.filter(is_archived=False)

    return render(request, 'pages/main.html', {'services': services,'services_by_category': services_by_category, 'doctors': doctors, 'services':services})


def user_login(request):
    errors = {}

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(username=cd['username'], password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    next_url = request.POST.get('next') or request.GET.get('next')
                    if next_url:
                        return redirect(next_url)  
                    return redirect('home')  
                else:
                    errors['message'] = 'Аккаунт отключен'
            else:
                errors['message'] = 'Неверный логин или пароль'
        else:
            errors['form'] = 'Пожалуйста, исправьте ошибки в форме.'
            errors['form_errors'] = form.errors
    else:
        form = LoginForm()

    next_url = request.GET.get('next', '')
    return render(request, 'pages/login.html', {'form': form, 'errors': errors, 'next': next_url})


def register_patient(request):
    errors = {}  
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                return redirect('profile')  
            except Exception as e:
                errors['message'] = f'Ошибка регистрации: {str(e)}'
        else:
            errors['form'] = 'Пожалуйста, исправьте ошибки в форме.'
            errors['form_errors'] = form.errors
    else:
        form = PatientRegistrationForm()

    return render(request, 'pages/register.html', {'form': form, 'errors': errors})


def logout_view(request):
    logout(request)
    return redirect('home')


@require_POST
@login_required
def create_or_update_communication_log(request, consultation_id):
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin):
        messages.error(request, "У вас нет прав для выполнения этого действия")
        return redirect('profile')
    
    consultation = get_object_or_404(Consultation, id=consultation_id, is_archived=False)
    
    status = request.POST.get('status')
    valid_statuses = ['success', 'no_answer', 'failed']
    
    if status not in valid_statuses:
        messages.error(request, "Недопустимый статус коммуникации")
        return redirect('profile')
    
    notes = request.POST.get('notes', '').strip()[:1000]  
    
    try:
        communication_log = consultation.communication_logs.filter(is_archived=False).last()
        
        if communication_log:
            communication_log.status = status
            communication_log.notes = notes
            communication_log.admin = request.user
            communication_log.called_at = timezone.now()  
            communication_log.save()
        else:
            CommunicationLog.objects.create(
                consultation=consultation,
                admin=request.user,
                status=status,
                notes=notes,
            )
            
    except Exception as e:
        messages.error(request, f"Произошла ошибка при сохранении журнала: {str(e)}")
        return redirect('profile')
    
    return redirect('profile')


@login_required
def profile(request):
    user = request.user
    consultations = None
    admin_consultations = None
    sort_by = request.GET.get('sort', 'appointment__date')
    filter_by = request.GET.get('filter', 'today')

    is_patient = user.is_patient()
    is_doctor = user.is_doctor()
    is_admin = user.is_admin() or user.is_staff or user.is_superuser
    show_admin_panel = is_admin

    def filter_consultations(queryset, filter_by, sort_by):
        if filter_by == 'today':
            today = date.today()
            queryset = queryset.filter(appointment__date=today)
        elif filter_by == 'past':
            queryset = queryset.filter(appointment__date__lt=timezone.now())
        elif filter_by == 'upcoming':
            queryset = queryset.filter(appointment__date__gte=timezone.now())
        return queryset.order_by(sort_by)

    if is_patient:
        consultations = Consultation.objects.filter(
            patient=user,
            is_archived=False
        ).select_related('doctor', 'service', 'appointment')
        consultations = filter_consultations(consultations, filter_by, sort_by)

    if is_doctor:
        try:
            doctor = user.doctors
            doctor_consultations = Consultation.objects.filter(
                doctor=doctor,
                is_archived=False
            ).select_related('patient', 'service', 'appointment')
            doctor_consultations = filter_consultations(doctor_consultations, filter_by, sort_by)
            consultations = doctor_consultations if consultations is None else consultations | doctor_consultations
        except Doctors.DoesNotExist:
            consultations = consultations or Consultation.objects.none()

    if is_admin:
        today = date.today()
        admin_consultations = Consultation.objects.filter(
            appointment__date=today,
            is_archived=False
        ).select_related('patient', 'doctor', 'service', 'appointment').prefetch_related('communication_logs').order_by('appointment__date')

    return render(request, 'pages/profile.html', {
        'user': user,
        'consultations': consultations,
        'admin_consultations': admin_consultations,
        'sort_by': sort_by,
        'filter_by': filter_by,
        'show_admin_panel': show_admin_panel,
    })


def services(request):    
    service_categories = ServiceСategories.objects.filter(is_archived=False)

    services_by_category = {}
    for category in service_categories:
        services_by_category[category] = Service.objects.filter(service_categories=category, is_archived=False)

    return render(request, 'pages/services.html', {'services': services,'services_by_category': services_by_category})


def doctors(request):    
    doctors = Doctors.objects.filter(is_archived=False)
    services = Service.objects.filter(is_archived=False)
    educations = Education.objects.filter(is_archived=False)

    return render(request, 'pages/doctors.html', {'doctors': doctors, 'services':services, 'educations':educations})


def articles(request):    
    articles = Articles.objects.filter(published=True, is_archived=False)

    articles_category = Articles.objects.filter(is_archived=False).values('category').distinct().order_by('category')

    category_filter = request.GET.get('articles_category', None)
    if category_filter:
        articles = articles.filter(category=category_filter)
    else:
        articles = articles.all()

    search_query = request.GET.get('q', '')
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(full_text__icontains=search_query)
        )
    else:
        articles = articles.all()

    current_time = timezone.now()

    for article in articles:
        if article.category == 'Акции и Скидки' and article.end_date:
            remaining_days = (article.end_date - current_time).days
            article.remaining_days = remaining_days if remaining_days > 0 else 0
        else:
            article.remaining_days = None

    return render(request, 'pages/articles.html', {'articles': articles, 'articles_category': articles_category})


def article_detail(request, pk):
    article = get_object_or_404(Articles, pk=pk, published=True, is_archived=False)

    similar_articles = Articles.objects.filter(category=article.category, is_archived=False).exclude(pk=article.pk)

    return render(request, 'pages/article_detail.html', {'article': article, 'similar_articles': similar_articles})


def contacts(request):    
    return render(request, 'pages/contacts.html')


# Создание консультаций 
@login_required
def create_consultation(request):
    errors = {}

    try:
        user = Patient.objects.get(pk=request.user.pk)
    except Patient.DoesNotExist:
        errors['auth'] = "Только пациенты могут записываться консультацию. Пожалуйста, зарегистрируйтесь как пациент."
    
    consultation_form = ConsultationForm(request.POST or None)

    if request.method == 'POST' and not errors:
        doctor_id = request.POST.get('doctor')
        date = request.POST.get('date')
        time = request.POST.get('time')

        doctor = Doctors.objects.filter(id=doctor_id).first()
        service_id = request.POST.get('service')
        service = Service.objects.filter(id=service_id).first()
        other_service = request.POST.get('other_service', '').strip()

        consultation_form = ConsultationForm(request.POST, doctor=doctor, date=date)

        doctor = Doctors.objects.filter(id=doctor_id).first() if doctor_id else None
        service = Service.objects.filter(id=service_id).first() if service_id else None


        if not consultation_form.is_valid():
            errors.update(consultation_form.errors)

        if user and not errors:
            existing_appointment = Consultation.objects.filter(
                patient=user,
                appointment__date=date,
                appointment__time=time
            ).exists()
            if existing_appointment:
                errors['appointment'] = "Вы уже записаны на это время. Пожалуйста, выберите другое время."
        
        if not errors:
            appointment = FreeTime.objects.filter(doctor=doctor, date=date, time=time).first()
            if not appointment:
                errors['appointment'] = "Выбранное время недоступно для этого врача."
            elif not service:
                errors['service'] = "Выбранная услуга не существует."
            else:
                Consultation.objects.create(
                    patient=user,
                    doctor=doctor,
                    service=service,
                    other_service=other_service,
                    appointment=appointment
                )
                messages.info(request, 'Вы успешно записались на консультацию. Подробнее посмотрите в профиле.')
                return redirect('create_consultation')

        return render(request, 'pages/consultation.html', {
                'errors': errors,
                'consultation_form': consultation_form
            })

    return render(request, 'pages/consultation.html', {
        'errors': errors,
        'consultation_form': consultation_form
    })


def get_services_dates(request, doctor_id):
    doctor = Doctors.objects.get(id=doctor_id)
    services = list(doctor.services.values('id', 'name'))
    dates = list(FreeTime.objects.filter(doctor=doctor).values_list('date', flat=True).distinct())
    return JsonResponse({'services': services, 'dates': dates})


def get_available_times(request, doctor_id, date):
    all_appointments = FreeTime.objects.filter(doctor_id=doctor_id, date=date).values_list('time', flat=True)

    booked_times = Consultation.objects.filter(
        appointment__doctor_id=doctor_id,
        appointment__date=date
    ).values_list('appointment__time', flat=True)

    available_times = [t for t in all_appointments if t not in booked_times]

    return JsonResponse({'times': available_times})


def get_services_for_doctor(request):
    doctor_id = request.GET.get('doctor_id')
    services = Service.objects.filter(doctors__id=doctor_id)
    services_data = [{"id": service.id, "name": service.name} for service in services]
    return JsonResponse(services_data, safe=False)
