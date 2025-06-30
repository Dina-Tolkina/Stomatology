from django.contrib import admin
from django.shortcuts import render, redirect
from .models import *
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from django.templatetags.static import static
from .forms import ScheduleForm
from django.urls import reverse, path
from django.db.models.functions import ExtractWeekDay
from django.contrib.admin.models import LogEntry, DELETION, CHANGE
from django.utils.encoding import force_str
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.admin import UserAdmin


class CustomAdminSite(admin.AdminSite):
    admin.site.site_header = "Страница администратора"
    admin.site.site_title = "Стомотология"
    admin.site.index_title = "Администрирование сайта"
    
    class Media:
        css = {
            'all': [static('admin/css/base.css')]  
        }

admin_site = CustomAdminSite(name='custom_admin')
admin.site.disable_action("delete_selected")

class ArchivedFilterAdmin(admin.ModelAdmin):
    change_list_template = "admin/with_archive_button.html"
    actions = ['archive_selected', 'restore_selected']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(self.model, 'is_archived'):
            if getattr(request, '_archived_only', False):
                return qs.filter(is_archived=True)
            return qs.filter(is_archived=False)
        return qs

    def log_action(self, request, obj, action_flag, message):
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.pk,
            object_repr=force_str(obj),
            action_flag=action_flag,
            change_message=message
        )

    @admin.action(description="Архивировать выбранные записи")
    def archive_selected(self, request, queryset):
        if hasattr(queryset.model, 'is_archived'):
            for obj in queryset:
                obj.is_archived = True
                obj.save()
                self.log_action(request, obj, DELETION, "Архивировано")
        self.message_user(request, "Выбранные записи архивированы.")

    @admin.action(description="Восстановить выбранные записи из архива")
    def restore_selected(self, request, queryset):
        if hasattr(queryset.model, 'is_archived'):
            for obj in queryset:
                obj.is_archived = False
                obj.save()
                self.log_action(request, obj, CHANGE, "Восстановлено из архива")
        self.message_user(request, "Выбранные записи восстановлены.")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'archived/',
                self.admin_site.admin_view(self.archived_view),
                name=f'{self.model._meta.app_label}_{self.model._meta.model_name}_archived'
            ),
        ]
        return custom_urls + urls

    def archived_view(self, request):
        request._archived_only = True
        return super().changelist_view(request, extra_context={
            'archived_mode': True,
            'title': f'Архивированные {self.model._meta.verbose_name_plural}',
        })

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        if getattr(request, '_archived_only', False):
            actions.pop('archive_selected', None)
        else:
            actions.pop('restore_selected', None)
        return actions

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and hasattr(obj, 'is_archived'):
            if request.method == 'POST':
                obj.is_archived = True
                obj.save()
                self.log_action(request, obj, DELETION, "Архивировано")
                self.message_user(request, f"Запись '{obj}' архивирована.")
                return redirect(
                    reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist')
                )

            extra_context = extra_context or {}
            extra_context.update({
                'title': 'Архивировать запись',
                'action': 'архивировать',
                'delete_button': 'Архивировать',
                'object': obj,
                'opts': self.model._meta,
                'app_label': self.model._meta.app_label,
            })
            return render(request, 'admin/delete_confirmation.html', extra_context)

        return super().delete_view(request, object_id, extra_context)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj and hasattr(obj, 'is_archived') and obj.is_archived:
            return readonly_fields + ('is_archived',)
        return readonly_fields

    def get_exclude(self, request, obj=None):
        exclude = super().get_exclude(request, obj) or []
        return exclude + ['is_archived']



class PatientAdmin(ArchivedFilterAdmin):
    list_display = ("first_name","last_name", "phone_number","email")
    search_fields = ('last_name', 'first_name', 'email')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (('Личная информация'), {'fields': ('first_name', 'last_name', 'patronymic', 'phone_number', 'email')}),
        (('Права доступа'), {'fields': ('is_active', 'is_staff', 'groups')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name', 'last_name', 'patronymic', 'phone_number', 'email', 'is_active', 'is_staff', 'groups'),
        }),
    )


class DoctorsAdmin(ArchivedFilterAdmin):
    list_display = ("last_name", "patronymic", "specializations_list", "email", "image_show")
    search_fields = ('last_name', 'first_name', 'email') 
    filter_horizontal = ('specializations', 'education')
    list_filter = ('specializations',)

    def specializations_list(self, obj):
        return ", ".join([s.name for s in obj.specializations.all()])
    specializations_list.short_description = 'Специализация'

    def image_show(self, obj):
        if obj.photo:
            return mark_safe("<img src='{}' width='200' />".format(obj.photo.url))
        return "None"

    image_show.__name__ = "Фото"


class ServiceAdmin(ArchivedFilterAdmin):
    list_display = ('name', 'service_categories', 'price')  
    filter_horizontal = ('doctors',)  
    search_fields = ('name', 'price')
    list_filter = ('service_categories', 'doctors')

    
class WeekdayFilter(SimpleListFilter):
    title = 'День недели'
    parameter_name = 'weekday'

    WEEKDAYS = [
        ('0', 'Понедельник'),
        ('1', 'Вторник'),
        ('2', 'Среда'),
        ('3', 'Четверг'),
        ('4', 'Пятница'),
        ('5', 'Суббота'),
        ('6', 'Воскресенье'),
    ]

    DAY_OF_WEEK = {
        '0': 2, 
        '1': 3,  
        '2': 4,  
        '3': 5,  
        '4': 6,  
        '5': 7,  
        '6': 1,  
    }

    def lookups(self, request, model_admin):
        return self.WEEKDAYS

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            return queryset.annotate(
                weekday=ExtractWeekDay('date')
            ).filter(weekday=self.DAY_OF_WEEK.get(value))
        return queryset
    

class FreeTimeAdmin(ArchivedFilterAdmin):
    list_display = ('doctor', 'date', 'time')
    list_filter = ['doctor', 'date', WeekdayFilter]
    search_fields = ('date', 'time',)
    autocomplete_fields = ('doctor',)
    ordering = ('date', 'time')
    change_list_template = "admin/freetime_change_list.html" 

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['create_schedule_url'] = reverse('admin:create_schedule')
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('create-schedule/', self.admin_site.admin_view(self.create_schedule), name='create_schedule'),
        ]
        return custom_urls + urls

    def create_schedule(self, request):
        if request.method == 'POST':
            form = ScheduleForm(request.POST)
            if form.is_valid():
                doctors = form.cleaned_data['doctors']
                dates = form.cleaned_data['dates']
                times = form.cleaned_data['times']
                for doctor in doctors:
                    for date in dates:
                        for t in times:
                            FreeTime.objects.create(doctor=doctor, date=date, time=t)
                self.message_user(request, "Расписание успешно создано!")
                return redirect('..')
        else:
            form = ScheduleForm()

        return render(request, 'admin/create_schedule.html', {'form': form})
     

class ConsultationAdmin(ArchivedFilterAdmin):
    autocomplete_fields = ('patient', 'doctor', 'service')
    list_display = ('patient', 'doctor', 'service_or_other', 'appointment_date', 'appointment_time')
    list_filter = ('doctor', 'appointment__date')
    search_fields = ('patient__full_name', 'doctor__full_name', 'service__name', 'other_service')
    ordering = ('appointment__date', 'appointment__time')
  
    def service_or_other(self, obj):
        return obj.other_service if obj.other_service else obj.service
    service_or_other.short_description = 'Услуга'

    def appointment_date(self, obj):
        return obj.appointment.date
    appointment_date.short_description = 'Дата приема'
    
    def appointment_time(self, obj):
        return obj.appointment.time
    appointment_time.short_description = 'Время приема'
    

class ArticlesAdmin(ArchivedFilterAdmin):
    list_display = ('title', 'category', 'publication_date', 'end_date', 'published')
    search_fields = ('title', 'publication_date')
    list_filter = ('category',)
    list_editable = ('published',)
   

@admin.register(User)
class CustomUserAdmin(UserAdmin, ArchivedFilterAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'date_joined', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')
    
    fieldsets = (
        (None, {'fields': ['username']}),
        (('Персональная информация'), {'fields': ('first_name', 'last_name', 'patronymic', 'phone_number', 'email')}),
        (('Разрешения'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (('Важные даты'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('first_name', 'last_name', 'patronymic', 'email', 'phone_number')
        }),
        (('Права доступа'), {'fields': ('is_active', 'is_staff', 'groups')}),
    )


admin.site.register(Patient, PatientAdmin)
admin.site.register(Specialization, ArchivedFilterAdmin)
admin.site.register(Doctors, DoctorsAdmin)
admin.site.register(ServiceСategories, ArchivedFilterAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(FreeTime, FreeTimeAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Education, ArchivedFilterAdmin)
admin.site.register(Articles, ArticlesAdmin)
admin.site.register(CommunicationLog, ArchivedFilterAdmin)