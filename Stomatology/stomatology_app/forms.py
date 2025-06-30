from django import forms
from .models import *
from django.core.exceptions import ValidationError
from django.utils.timezone import localtime, now
from datetime import datetime
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _


class LoginForm(forms.Form):
    username = forms.CharField(max_length=30, label='Имя пользователя')
    password = forms.CharField(max_length=30, label='Пароль', widget=forms.PasswordInput)

    
class PatientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='Имя')
    last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    patronymic = forms.CharField(required=False, label="Отчество", widget=forms.TextInput())
    email = forms.EmailField(required=True, label='Электронная почта')
    phone_number = forms.CharField(max_length=20, required=True, label='Телефон')

    class Meta:
        model = Patient
        fields = ('username', 'first_name', 'last_name', 'patronymic', 'email', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
        self.fields['email'].help_text = ''
        self.fields['first_name'].help_text = ''
        self.fields['last_name'].help_text = ''

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise forms.ValidationError(_("Имя пользователя не может быть пустым."))
        if ' ' in username:
            raise forms.ValidationError(_("Имя пользователя не может содержать пробелы."))
        if not all(char.isalnum() or char in '@.+_-' for char in username):
            raise forms.ValidationError(
                _("Имя пользователя может содержать только буквы, цифры и символы @/./+/-/_"),
                code='invalid_username'
            )
        if Patient.objects.filter(username=username).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError(
                _("Это имя пользователя уже занято."),
                code='username_taken'
            )
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Patient.objects.filter(email=email).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError(
                _("Эта электронная почта уже зарегистрирована."),
                code='email_taken'
            )
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if Patient.objects.filter(phone_number=phone_number).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError(
                _("Этот номер телефона уже зарегистрирован."),
                code='phone_number_taken'
            )
        return phone_number

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                _("Введенные пароли не совпадают. Пожалуйста, введите одинаковые пароли."),
                code='password_mismatch'
            )
        return password2
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not all(char.isalpha() for char in first_name):
            raise forms.ValidationError(
                _("Имя может содержать только буквы."),
                code='invalid_first_name'
            )
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not all(char.isalpha() for char in last_name):
            raise forms.ValidationError(
                _("Фамилия может содержать только буквы."),
                code='invalid_last_name'
            )
        return last_name

    def clean_patronymic(self):
        patronymic = self.cleaned_data.get('patronymic')
        if patronymic and not all(char.isalpha() for char in patronymic):
            raise forms.ValidationError(
                _("Отчество может содержать только буквы."),
                code='invalid_patronymic'
            )
        return patronymic
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.patronymic = self.cleaned_data['patronymic']

        if commit:
            try:
                user.save()
                patient_group, created = Group.objects.get_or_create(name='Пациенты')
                user.groups.add(patient_group)
            except Exception as e:
                raise forms.ValidationError(f'Ошибка при сохранении пользователя: {str(e)}')

        return user
    

#Запись на прием к врачу
class ConsultationForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(
        queryset=Doctors.objects.all(),
        label="Врач",
        empty_label="Выберите врача", 
        error_messages={'required': 'Пожалуйста, выберите врача.'},
        widget=forms.Select(attrs={'id': 'id_doctor'})
    )
    service = forms.ModelChoiceField(
        queryset=Service.objects.none(),
        required=True,
        label="Оказываемая услуга",
        empty_label="Сначала выберите врача",  
        error_messages={'required': 'Пожалуйста, выберите услугу.'},
        widget=forms.Select(attrs={'id': 'id_service' , 'onchange': 'toggleOtherService()', 'disabled': 'disabled'})
    )
    other_service = forms.CharField(
        required=False,
        label="Другая услуга",
        widget=forms.TextInput(attrs={'id': 'id_other_service', 'display': 'none'})
    )
    date = forms.DateField(
        required=True,
        label="Дата консультации",
        error_messages={'required': 'Пожалуйста, выберите дату.'},
        widget=forms.TextInput(attrs={
            'id': 'id_date',
            'type': 'text',
            'class': 'custom-date-input',
            'onchange': 'updateTimes()',
            'placeholder': 'Сначала выберите услугу',
            'disabled': 'disabled'  
        })
    )
    time = forms.CharField(
        required=True,
        label="Время консультации",
        error_messages={'required': 'Пожалуйста, выберите время.'},
        widget=forms.TextInput(attrs={
            'id': 'id_time',
            'class': 'time-input',
            'disabled': 'disabled',
            'placeholder': 'Сначала выберите дату'
        })
    )

    class Meta:
        model = Consultation
        fields = ['doctor', 'service', 'other_service', 'date', 'time']

    def __init__(self, *args, doctor=None, date=None, **kwargs):
        super().__init__(*args, **kwargs)

        if doctor:
            self.fields['service'].queryset = doctor.services.all()

            available_dates = FreeTime.objects.filter(doctor=doctor).values_list('date', flat=True).distinct()
            self.fields['date'].widget.choices = [(d, d) for d in available_dates]

        if doctor and date:
            all_appointments = FreeTime.objects.filter(doctor=doctor, date=date).values_list('time', flat=True)
            booked_times = Consultation.objects.filter(
                appointment__doctor=doctor, appointment__date=date
            ).values_list('appointment__time', flat=True)

            current_time = localtime(now()).time() if date == localtime(now()).date() else None

            def parse_time_range(time_range):
                return datetime.strptime(time_range.split('-')[0], "%H:%M").time()

            self.fields['time'].choices = [
                (t, t) for t in all_appointments
                if t not in booked_times and (not current_time or parse_time_range(t) > current_time)
            ]

        if 'time' in self.errors:
            self.data = self.data.copy()
            self.data['time'] = ''
            self.fields['time'].initial = ''
            self.fields['time'].widget.attrs.pop("disabled", None)
            self.fields['time'].widget.attrs['placeholder'] = 'Выберите доступное время'
            self.fields["service"].widget.attrs.pop("disabled", None)

        if self.errors.get("date") or self.data.get("service"):
            self.fields["date"].widget.attrs.pop("disabled", None)
            self.fields["date"].widget.attrs['placeholder'] = 'Выберите доступную дату'
            self.fields["service"].widget.attrs.pop("disabled", None)
        
    def clean_time(self):
        doctor = self.cleaned_data.get("doctor")
        date = self.cleaned_data.get("date")
        time = self.cleaned_data.get("time")

        if doctor and date and time:
            if Consultation.objects.filter(
                appointment__doctor=doctor,
                appointment__date=date,
                appointment__time=time
            ).exists():
                self.cleaned_data["time"] = ""
                raise ValidationError("Это время уже занято, выберите другое.")

            if date == localtime(now()).date():
                time_obj = datetime.strptime(time.split('-')[0], "%H:%M").time()
                if time_obj <= localtime(now()).time():
                    self.cleaned_data["time"] = ""
                    raise ValidationError("Нельзя выбрать прошедшее время.")

        return time
    
# Форма для добавление доступных временных слотов массового добавления (врачей, дат и времени)           
class ScheduleForm(forms.Form):
    doctors = forms.ModelMultipleChoiceField(
        queryset=Doctors.objects.all(),
        label="Врачи",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'doctor-checkbox', 'aria-label': 'Выберите врачей'})
    )
    dates = forms.CharField(
        label="Даты",
        widget=forms.TextInput(attrs={'class': 'flatpickr', 'style': 'display:none;'})
    )
    times = forms.MultipleChoiceField(
        choices=AVAILABLE_TIMES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'time-checkbox'}),
        label="Время"
    )

    def clean_dates(self):
        raw = self.cleaned_data.get('dates', '')
        if not raw:
            raise forms.ValidationError("Выберите хотя бы одну дату.")
        
        date_strings = [d.strip() for d in raw.split(',') if d.strip()]
        if not date_strings:
            raise forms.ValidationError("Выберите хотя бы одну дату.")
        
        try:
            return [datetime.strptime(d, "%Y-%m-%d").date() for d in date_strings]
        except ValueError:
            raise forms.ValidationError("Неверный формат дат. Используйте календарь.")
