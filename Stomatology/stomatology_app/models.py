from django.db import models
from django.core.validators import RegexValidator
from django_ckeditor_5.fields import CKEditor5Field
from smart_selects.db_fields import ChainedForeignKey
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager


class User(AbstractUser):
    patronymic = models.CharField(max_length=50, unique=False,verbose_name = ("Отчество"),  validators=[RegexValidator(r'^[a-zA-ZА-Яа-яЁё]+$', 'Разрешены только буквы.')])
    phone_number = models.CharField(max_length=20, blank=True, verbose_name = ("Номер телефона"))
    is_archived = models.BooleanField(default=False)
    
    def is_patient(self):
        return self.groups.filter(name='Пациенты').exists()
    
    def is_admin(self):
        return self.groups.filter(name='Администраторы').exists()
    
    def is_doctor(self):
        return self.groups.filter(name='Врачи').exists()
    

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    

class PatientManager(UserManager): 
    def get_queryset(self):
        return super().get_queryset().filter(groups__name='Пациенты')
    

class Patient(User):
    objects = PatientManager()

    class Meta:
        proxy=True
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name = ("Название"))
    is_archived = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Специализация"
        verbose_name_plural = "Специализации"


class ServiceСategories(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name = ("Название"))
    photo = models.ImageField(upload_to='service_categories/', blank=True, null=True, verbose_name = ("Фото категории"))
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Категория услуги"
        verbose_name_plural = "Категории услуг"


class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name = ("Название"))
    service_categories = models.ForeignKey(ServiceСategories, on_delete=models.SET_NULL, null=True, blank=True, verbose_name = ("Категория услуги"))
    doctors = models.ManyToManyField('Doctors', related_name='services', verbose_name="Врачи")
    description = models.TextField(null=True, blank=True, verbose_name = ("Описание"))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name = ("Цена"))
    photo = models.ImageField(upload_to='service/', blank=True, null=True, verbose_name = ("Фото услуги"))
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"


class Education(models.Model):
    institution = models.CharField(max_length=200, verbose_name="Учебное заведение")
    degree = models.CharField(max_length=200, verbose_name="Степень/Специальность")
    year_of_graduation = models.IntegerField(verbose_name="Год окончания")
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.institution} ({self.degree}, {self.year_of_graduation})"

    class Meta:
        verbose_name = "Образование"
        verbose_name_plural = "Образование"


class Doctors(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name = ("Аккаунт"))
    first_name = models.CharField(max_length=50, unique=False,verbose_name = ("Имя"),  validators=[RegexValidator(r'^[a-zA-ZА-Яа-яЁё]+$', 'Разрешены только буквы.')])
    last_name = models.CharField(max_length=50, unique=False,verbose_name = ("Фамилия"),  validators=[RegexValidator(r'^[a-zA-ZА-Яа-яЁё]+$', 'Разрешены только буквы.')])
    patronymic = models.CharField(max_length=50, unique=False,verbose_name = ("Отчество"),  validators=[RegexValidator(r'^[a-zA-ZА-Яа-яЁё]+$', 'Разрешены только буквы.')])
    photo = models.ImageField(upload_to='doctors/', blank=True, null=True, verbose_name = ("Фото врача"))
    specializations = models.ManyToManyField(Specialization, blank=True, verbose_name=("Специализации"))
    phone_number = models.CharField(max_length=15, null=True, blank=True, verbose_name = ("Номер телефона"))
    email = models.EmailField(max_length=100, null=True, blank=True, verbose_name = ("Почта"))
    experience = models.PositiveIntegerField(verbose_name="Стаж работы (лет)", default=0)
    education = models.ManyToManyField(Education, blank=True, verbose_name="Образование")
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        verbose_name = "Врач"
        verbose_name_plural = "Врачи"


AVAILABLE_TIMES = [
    ("09:00-09:30", "09:00-09:30"), ("09:30-10:00", "09:30-10:00"), ("10:00-10:30", "10:00-10:30"), 
    ("10:30-11:00", "10:30-11:00"), ("11:00-11:30", "11:00-11:30"), ("11:30-12:00", "11:30-12:00"), 
    ("12:00-12:30", "12:00-12:30"), ("12:30-13:00", "12:30-13:00"), ("13:00-13:30", "13:00-13:30"), 
    ("13:30-14:00", "13:30-14:00"), ("14:00-14:30", "14:00-14:30"), ("14:30-15:00", "14:30-15:00"), 
    ("15:00-15:30", "15:00-15:30"), ("15:30-16:00", "15:30-16:00"), ("16:00-16:30", "16:00-16:30"), 
    ("16:30-17:00", "16:30-17:00"), ("17:00-17:30", "17:00-17:30"), ("17:30-18:00", "17:30-18:00"), 
    ("18:00-18:30", "18:00-18:30"), ("18:30-19:00", "18:30-19:00"), ("19:00-19:30", "19:00-19:30"), 
    ("19:30-20:00", "19:30-20:00"), ("20:00-20:30", "20:00-20:30"), ("20:30-21:00", "20:30-21:00"),
]

class FreeTime(models.Model):
    doctor = models.ForeignKey('Doctors', on_delete=models.CASCADE, verbose_name="Врач")
    date = models.DateField(verbose_name="Дата")
    time = models.CharField(choices=AVAILABLE_TIMES,  max_length=20, verbose_name="Время")
    is_archived = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Доступное время приема"
        verbose_name_plural = "Доступное время приемов"
    
    def __str__(self):
        return f"{self.doctor} - {self.date} {self.time}"


class Consultation(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, verbose_name="Пациент")
    doctor = models.ForeignKey('Doctors', on_delete=models.CASCADE, verbose_name="Врач")
    service = models.ForeignKey('Service', on_delete=models.CASCADE, verbose_name="Услуга")
    other_service = models.CharField(max_length=255, null=True, blank=True, verbose_name="Другая услуга")  
    is_archived = models.BooleanField(default=False)
    appointment = ChainedForeignKey(
        FreeTime,
        chained_field="doctor", 
        chained_model_field="doctor",  
        show_all=False,  
        auto_choose=True,  
        sort=True,  
        verbose_name="Запись на прием"
    )

    class Meta:
        verbose_name = "Консультация"
        verbose_name_plural = "Консультации"

    def __str__(self):
        return f"{self.patient} - {self.service or self.other_service} - {self.doctor}"        
    

class CommunicationLog(models.Model):
    status = models.CharField(
        max_length=50,
        choices=[
            ('success', 'Успешно'),
            ('no_answer', 'Нет ответа'),
            ('failed', 'Не удалось'),
        ],
        verbose_name="Статус звонка"
    )
    consultation = models.ForeignKey('Consultation', on_delete=models.CASCADE, related_name='communication_logs', verbose_name="Консультация")
    admin = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, verbose_name="Администратор")
    called_at = models.DateTimeField(auto_now_add=True, verbose_name="Время звонка")
    notes = models.TextField(blank=True, null=True, verbose_name="Примечания")
    is_archived = models.BooleanField(default=False, verbose_name="Архивировано")

    class Meta:
        verbose_name = "Журнал коммуникаций"
        verbose_name_plural = "Журналы коммуникаций"

    def __str__(self):
        return f"Коммуникация для {self.consultation} ({self.status}) - {self.called_at}"
    

class Articles(models.Model):
    CATEGORY_ARTICLES = [
        ('Акции и Скидки', 'Акции и Скидки'),
        ('Новости клиники', 'Новости клиники'),
        ('Услуги и процедуры', 'Услуги и процедуры'),
        ('Полезные советы', 'Полезные советы'),
        ('Вопрос-ответ', 'Вопрос-ответ'),
    ]

    title = models.CharField(max_length=255, unique=True, blank=False, verbose_name = ("Заголовок"))
    description = models.CharField(max_length=255, blank=False, verbose_name=("Описание"))
    full_text = CKEditor5Field(config_name='extends', verbose_name=("Полный текст"))
    category = models.CharField(choices=CATEGORY_ARTICLES, max_length=50,blank=False, verbose_name="Категория")
    img = models.ImageField(upload_to='articles/', blank=False, verbose_name = ("Картинка статьи"))
    publication_date = models.DateTimeField(blank=False, verbose_name=("Дата публикации"))
    end_date = models.DateTimeField(null=True, blank=True, verbose_name=("Дата окончания"))
    published = models.BooleanField(default=True, verbose_name="Опубликовано")
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['-publication_date']
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"

    def __str__(self):
        return f"{self.title} - {self.category} {self.publication_date}"
