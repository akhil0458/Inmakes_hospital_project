from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# Custom User Model
class CustomUser(AbstractUser):
    is_patient = models.BooleanField(default=False)
    is_doctor = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    @property
    def full_name(self):
        if self.is_patient and hasattr(self, 'patientprofile'):
            return self.patientprofile.full_name
        elif self.is_doctor and hasattr(self, 'doctorprofile'):
            return self.doctorprofile.full_name
        elif self.is_admin and hasattr(self, 'adminprofile'):
            return self.adminprofile.full_name
        return f"{self.first_name} {self.last_name}".strip()


class AdminProfile(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=120)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20)
    address = models.TextField()

    def __str__(self):
        return self.full_name


# Doctor Profile
class DoctorProfile(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=120)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    specialization = models.CharField(max_length=100)
    available_days = models.CharField(max_length=100)

    def __str__(self):
        return f"Dr. {self.full_name} ({self.specialization})"



# Patient Profile
class PatientProfile(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=120)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    address = models.TextField()
    phone = models.CharField(max_length=15)  # Renamed from "contact" to match actual field
    medical_history = models.TextField(blank=True)

    def __str__(self):
        return self.full_name


# Appointment
class Appointment(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return f"Appointment {self.id} - {self.patient.full_name} with {self.doctor.full_name}"


# Medical History
class MedicalHistory(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, null=True, blank=True)
    diagnosis = models.CharField(max_length=255)
    treatment_history = models.TextField()
    medications = models.TextField()
    allergies = models.TextField(blank=True)
    date = models.DateField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.patient.full_name} - {self.diagnosis}"


# Prescription
class Prescription(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE)
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=255)
    frequency = models.CharField(max_length=255)
    duration = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)
    date_issued = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.medication_name} for {self.patient.full_name}"


# Billing
class Bill(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=20, choices=[('Cash', 'Cash'), ('Online', 'Online')], default='Cash')

    def __str__(self):
        return f"Bill #{self.id} - {self.patient.user.username}"

# Facility
class Facility(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    departments = models.CharField(max_length=100)
    resources = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# Health Education
class HealthEducationResource(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    date = models.DateField(auto_now_add=True)
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title


class HealthBulletin(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    date = models.DateField(auto_now_add=True)
    pdf = models.FileField(upload_to='bulletins/', blank=True, null=True)

    def __str__(self):
        return self.title



class MedicalResearch(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField()
    date = models.DateField(auto_now_add=True)
    document = models.FileField(upload_to='research_papers/', blank=True, null=True)

    def __str__(self):
        return self.title



class Publication(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)
    file = models.FileField(upload_to='publications/', blank=True, null=True)

    def __str__(self):
        return self.title


