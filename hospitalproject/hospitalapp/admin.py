from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    CustomUser, PatientProfile, DoctorProfile, AdminProfile,
    Appointment, MedicalHistory, Bill, Prescription
)
from .forms import AdminUserCreationForm, CustomUserChangeForm


class DoctorProfileInline(admin.StackedInline):
    model = DoctorProfile
    can_delete = False

class PatientProfileInline(admin.StackedInline):
    model = PatientProfile
    can_delete = False

class AdminProfileInline(admin.StackedInline):
    model = AdminProfile
    can_delete = False


class UserAdmin(BaseUserAdmin):
    add_form = AdminUserCreationForm
    form = CustomUserChangeForm

    list_display = ('username', 'email', 'is_staff', 'is_superuser', 'is_doctor', 'is_patient', 'is_admin')
    list_filter = ('is_doctor', 'is_patient', 'is_admin', 'is_staff', 'is_superuser')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('User Roles', {'fields': ('is_doctor', 'is_patient', 'is_admin')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('User Roles', {'fields': ('is_doctor', 'is_patient', 'is_admin')}),
    )

    inlines = [DoctorProfileInline, PatientProfileInline, AdminProfileInline]


# Register everything
admin.site.register(CustomUser, UserAdmin)
admin.site.register(PatientProfile)
admin.site.register(DoctorProfile)
admin.site.register(AdminProfile)
admin.site.register(Appointment)
admin.site.register(MedicalHistory)
admin.site.register(Bill)
admin.site.register(Prescription)
