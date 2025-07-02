import stripe
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.core.exceptions import ObjectDoesNotExist

from django.conf import settings
from hospitalproject import settings
from .models import Facility, DoctorProfile, PatientProfile, Appointment, MedicalHistory, Bill, HealthEducationResource, \
    AdminProfile, CustomUser, Prescription, Announcement, HealthBulletin, MedicalResearch, Publication
from .forms import (
    UserRegisterForm, UserCreationForm,
    PatientProfileForm, DoctorProfileForm,

    AdminUserCreationForm, CustomUserChangeForm,
    FacilityForm, PrescriptionForm, BillingForm, HealthEducationResourceForm,
    AdminCreationForm
)

User = get_user_model()

# --- Decorators ---
def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_admin:
            messages.error(request, "Admins only.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# --- Views ---

def home(request):
    return render(request, 'base.html')


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_patient = True
            user.save()

            PatientProfile.objects.create(
                user=user,
                full_name=form.cleaned_data['full_name'],
                age=form.cleaned_data['age'],
                gender=form.cleaned_data['gender'],
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address']
            )

            messages.success(request, "Registration successful. Please log in.")
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

@admin_required
def create_user_with_profile(request, user_form_class, profile_form_class, role_flags, template_name):
    if request.method == 'POST':
        user_form = user_form_class(request.POST)
        profile_form = profile_form_class(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            for attr, val in role_flags.items():
                setattr(user, attr, val)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            messages.success(request, f'User {user.username} created successfully!')
            return redirect('manage_users')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = user_form_class()
        profile_form = profile_form_class()

    return render(request, template_name, {
        'user_form': user_form,
        'profile_form': profile_form
    })


@admin_required
def create_patient(request):
    return create_user_with_profile(
        request,
        UserCreationForm,
        PatientProfileForm,
        {'is_patient': True, 'is_doctor': False, 'is_admin': False},
        'admin/create_patient.html'
    )



def create_doctor(request):
    if request.method == 'POST':
        user_form = UserCreationForm(request.POST)
        profile_form = DoctorProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.is_doctor = True
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            messages.success(request, 'Doctor created successfully.')
            return redirect('admin_dashboard')
    else:
        user_form = UserCreationForm()
        profile_form = DoctorProfileForm()

    return render(request, 'admin/create_doctor.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@admin_required
def create_admin(request):
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            # Save user
            user = CustomUser.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                is_admin=True
            )

            # Save admin profile
            AdminProfile.objects.create(
                user=user,
                full_name=form.cleaned_data['full_name'],
                age=form.cleaned_data['age'],
                gender=form.cleaned_data['gender'],
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address']
            )

            messages.success(request, 'Admin created successfully.')
            return redirect('manage_users')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AdminCreationForm()

    return render(request, 'admin/create_admin.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_admin:
                return redirect('admin_dashboard')
            elif user.is_doctor:
                return redirect('doctor_dashboard')
            elif user.is_patient:
                return redirect('patient_dashboard')
            else:
                messages.error(request, "User role undefined.")
                logout(request)
                return redirect('login')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'login/login.html')


@login_required
def patient_dashboard(request):
    try:
        patient = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        return render(request, 'patient_dashboard.html', {'error': 'Patient profile not found.'})

    # Fetch related data
    appointments = Appointment.objects.filter(patient=patient).order_by('-date')
    medical_history = MedicalHistory.objects.filter(patient=patient).order_by('-date')
    prescriptions = Prescription.objects.filter(patient=patient).order_by('-date_issued')
    bills = Bill.objects.filter(patient=patient).order_by('-date')
    resources = HealthEducationResource.objects.all()

    context = {
        'patient': patient,
        'appointments': appointments,
        'medical_history': medical_history,
        'prescriptions': prescriptions,
        'bills': bills,
        'resources': resources,
    }

    return render(request, 'patient/patient_dashboard.html', context)

@login_required
def doctor_dashboard(request):
    return render(request, 'doctor/dashboard.html')


@admin_required
def admin_dashboard(request):
    return render(request, 'admin/dashboard.html')


@admin_required
def manage_users(request):
    users = CustomUser.objects.select_related(
        'patientprofile', 'doctorprofile', 'adminprofile'
    ).all()

    return render(request, 'admin/manage_users.html', {'users': users})


@admin_required
def manage_facilities(request):
    facilities = Facility.objects.all()
    return render(request, 'admin/manage_facilities.html', {'facilities': facilities})


@login_required
def manage_appointments(request):
    appointments = Appointment.objects.select_related('patient', 'doctor').all().order_by('-date', '-time')
    return render(request, 'admin/admin_appointments.html', {'appointments': appointments})


@admin_required
def create_user(request):
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_doctor = form.cleaned_data.get('is_doctor')
            user.is_patient = form.cleaned_data.get('is_patient')
            user.is_admin = form.cleaned_data.get('is_admin')
            user.save()

            # Common profile data
            full_name = form.cleaned_data.get('full_name')
            age = form.cleaned_data.get('age')
            gender = form.cleaned_data.get('gender')
            phone = form.cleaned_data.get('phone')
            address = form.cleaned_data.get('address')

            if user.is_doctor:
                specialization = form.cleaned_data.get('specialization', '')
                DoctorProfile.objects.create(
                    user=user,
                    full_name=full_name,
                    age=age,
                    gender=gender,
                    phone=phone,
                    address=address,
                    specialization=specialization,
                    available_days=''  # Optional: handle separately if needed
                )
            elif user.is_patient:
                PatientProfile.objects.create(
                    user=user,
                    full_name=full_name,
                    age=age,
                    gender=gender,
                    phone=phone,
                    address=address,
                    medical_history=''
                )
            elif user.is_admin:
                AdminProfile.objects.create(
                    user=user,
                    full_name=full_name,
                    age=age,
                    gender=gender,
                    phone=phone,
                    address=address
                )

            messages.success(request, f'User {user.username} created successfully!')
            return redirect('manage_users')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AdminUserCreationForm()

    return render(request, 'admin/user_create.html', {'form': form})

@admin_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('manage_users')
    else:
        form = CustomUserChangeForm(instance=user)
    return render(request, 'admin/user_edit.html', {'form': form, 'user_id': user_id})


@admin_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('manage_users')
    return render(request, 'admin/user_delete.html', {'user': user})


@admin_required
def add_facility(request):
    if request.method == 'POST':
        form = FacilityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Facility added successfully.")
            return redirect('manage_facilities')
    else:
        form = FacilityForm()
    return render(request, 'admin/facility_create.html', {'form': form})


@admin_required
def edit_facility(request, id):
    facility = get_object_or_404(Facility, id=id)
    if request.method == 'POST':
        form = FacilityForm(request.POST, instance=facility)
        if form.is_valid():
            form.save()
            messages.success(request, 'Facility updated successfully.')
            return redirect('manage_facilities')
    else:
        form = FacilityForm(instance=facility)
    return render(request, 'admin/facility_edit.html', {'form': form, 'facility': facility})


@admin_required
def delete_facility(request, id):
    facility = get_object_or_404(Facility, id=id)
    if request.method == 'POST':
        facility.delete()
        messages.success(request, 'Facility deleted successfully.')
        return redirect('manage_facilities')
    return render(request, 'admin/facility_delete.html', {'facility': facility})



@login_required
def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def book_appointment(request):
    if request.method == 'POST':
        try:
            patient_profile = request.user.patientprofile
        except ObjectDoesNotExist:
            messages.error(request, "Patient profile not found. Please contact support.")
            return redirect('patient_dashboard')

        doctor_id = request.POST.get('doctor')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        reason = request.POST.get('reason')

        doctor = get_object_or_404(DoctorProfile, id=doctor_id)

        Appointment.objects.create(
            patient=patient_profile,
            doctor=doctor,
            date=appointment_date,
            time=appointment_time,
            reason=reason,
            status='Pending'
        )

        messages.success(request, "Appointment booked successfully.")
        return redirect('patient_dashboard')

    doctors = DoctorProfile.objects.select_related('user').order_by('user__first_name')
    return render(request, 'patient/book_appointment.html', {'doctors': doctors})


@login_required
def doctor_list(request):
    doctors = DoctorProfile.objects.all()
    return render(request, 'doctor/doctor_list.html', {'doctors': doctors})


# View for patient management
def patient_management(request):
    patients = PatientProfile.objects.all()
    return render(request, 'doctor/patient_management.html', {'patients': patients})


# View for viewing a specific appointment
def doctor_appointments(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    return render(request, 'doctor/view_appointment.html', {'appointment': appointment})


@login_required
def prescribe(request):
    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)

            # Get doctor profile from the logged-in user
            try:
                doctor_profile = request.user.doctorprofile
            except DoctorProfile.DoesNotExist:
                messages.error(request, "You are not authorized to prescribe.")
                return redirect('dashboard')  # or another safe page

            prescription.doctor = doctor_profile
            prescription.save()

            messages.success(request, "Prescription created successfully.")
            return redirect('doctor_dashboard')
    else:
        form = PrescriptionForm()

    return render(request, 'doctor/prescribe_medication.html', {'form': form})



# View for viewing a specific patient
def view_patient(request, patient_id):
    patient = get_object_or_404(PatientProfile, id=patient_id)
    return render(request, 'doctor/view_patient.html', {'patient': patient})

# View for editing patient info
def edit_patient(request, patient_id):
    patient = get_object_or_404(PatientProfile, id=patient_id)
    return render(request, 'doctor/edit_patient.html', {'patient': patient})

# View for deleting a patient
def delete_patient(request, patient_id):
    patient = get_object_or_404(PatientProfile, id=patient_id)
    patient.delete()
    return redirect('patient_management')



def create_appointment(request):
    # Logic for creating an appointment
    return HttpResponse("Create Appointment Page")

def view_appointment(request, patient_id):
    appointments = Appointment.objects.filter(patient__id=patient_id)
    return render(request, 'patient/view_appointments.html', {'appointments': appointments})

# View for deleting an appointment (can be extended)
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.delete()
    return redirect('appointments')


def edit_patient(request, patient_id):
    patient = get_object_or_404(PatientProfile, id=patient_id)
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            return redirect('patient_management')
    else:
        form = PatientProfileForm(instance=patient)

    return render(request, 'doctor/edit_patient.html', {'form': form})


@login_required
def doctor_appointments(request):
    try:
        doctor = request.user.doctorprofile
    except ObjectDoesNotExist:
        return render(request, 'error.html', {
            'message': 'Doctor profile not found. Please contact admin.'
        })

    appointments = Appointment.objects.filter(doctor=doctor).order_by('-date')
    return render(request, 'doctor/appointments.html', {
        'appointments': appointments
    })

@login_required
def view_medical_history(request, pk):
    history = get_object_or_404(MedicalHistory, pk=pk)
    return render(request, 'patient/view_medical_history.html', {'history': history})


@login_required
def view_bills(request,bill_id):
    try:
        patient = request.user.patientprofile
    except:
        return render(request, 'error.html', {'message': 'Only patients can view bills.'})

    bills = Bill.objects.filter(patient=patient).order_by('-date')

    return render(request, 'patient/view_bills.html', {'bills': bills})

def education_view(request):
    return render(request, 'patient/education.html')



@require_POST
def update_appointment_status(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    new_status = request.POST.get('status')

    if new_status in ['Confirmed', 'Declined', 'Completed']:
        appointment.status = new_status
        appointment.save()

        # If marked as Completed, create MedicalHistory record if not already added
        if new_status == 'Completed':
            MedicalHistory.objects.get_or_create(
                patient=appointment.patient,
                diagnosis=f' Dr. {appointment.doctor.user.get_full_name()}',
                treatment_history='Completed consultation',
                medications='Prescribed during consultation',
                allergies='None reported',
                defaults={'date': appointment.date}
            )

    return redirect('doctor_appointments')


@login_required
def delete_medical_history(request, record_id):
    record = get_object_or_404(MedicalHistory, id=record_id)

    # Optional: ensure only patient who owns the record can delete it
    if record.patient.user != request.user:
        messages.error(request, "You are not authorized to delete this record.")
        return redirect('patient_dashboard')

    record.delete()
    messages.success(request, "Medical history record deleted.")
    return redirect('patient_dashboard')



@login_required
def create_bill(request, patient_id):
    patient = get_object_or_404(PatientProfile, id=patient_id)
    doctors = DoctorProfile.objects.all()

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        amount = request.POST.get('amount')
        description = request.POST.get('description')

        if doctor_id and amount and description:
            doctor = get_object_or_404(DoctorProfile, id=doctor_id)

            Bill.objects.create(
                patient=patient,
                doctor=doctor,
                amount=amount,
                description=description,
                payment_method='cash',  # default to 'cash'
                paid=False  # default unpaid
            )

            messages.success(request, 'Bill created successfully.')
            return redirect('patient_management')  # or another appropriate redirect
        else:
            messages.error(request, 'Please fill in all fields.')

    return render(request, 'doctor/create_bill.html', {
        'patient': patient,
        'doctors': doctors,
    })


stripe.api_key = settings.STRIPE_SECRET_KEY
@login_required
def pay_bill(request, bill_id):
    patient = request.user.patientprofile
    bill = get_object_or_404(Bill, id=bill_id, patient=patient)

    # Set your Stripe secret key
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Create a Stripe Checkout Session
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'inr',
                'product_data': {
                    'name': f'Bill Payment for {patient.user.get_full_name()}',
                },
                'unit_amount': int(bill.amount * 100),  # amount in paisa
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri('/payment-success/'),
        cancel_url=request.build_absolute_uri('/payment-cancelled/'),
    )

    return render(request, 'stripe_checkout.html', {
        'session_id': session.id,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
        'bill': bill,
    })


def add_resource(request):
    if request.method == 'POST':
        form = HealthEducationResourceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = HealthEducationResourceForm()
    return render(request, 'admin/add_resources.html', {'form': form})


def manage_resources(request):
    resources = HealthEducationResource.objects.all()
    return render(request, 'admin/manage_resources.html', {'resources': resources})

def edit_resource(request, resource_id):
    resource = get_object_or_404(HealthEducationResource, id=resource_id)
    if request.method == 'POST':
        form = HealthEducationResourceForm(request.POST, instance=resource)
        if form.is_valid():
            form.save()
            return redirect('manage_resources')
    else:
        form = HealthEducationResourceForm(instance=resource)
    return render(request, 'admin/edit_resource.html', {'form': form})

def delete_resource(request, resource_id):
    resource = get_object_or_404(HealthEducationResource, id=resource_id)
    resource.delete()
    return redirect('manage_resources')


@login_required
def view_prescription(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk, patient__user=request.user)
    return render(request, 'patient/view_prescription.html', {'prescription': prescription})


def about_us(request):
    return render(request, 'home_data/about_us.html')


def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()

        if not (name and email and message):
            messages.error(request, "All fields are required.")
        else:
            # Optional: send an email or save to database
            # Example email send:
            try:
                send_mail(
                    subject=f"Contact Form from {name}",
                    message=message,
                    from_email=email,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],  # Set in settings.py
                    fail_silently=False,
                )
                messages.success(request, "Thank you for reaching out. We'll get back to you soon!")
                return redirect('contact')
            except Exception as e:
                messages.error(request, f"Failed to send message: {e}")

    return render(request, 'home_data/contact_us.html')



def announcements(request):
    announcements_list = Announcement.objects.order_by('-date')
    return render(request, 'home_data/announcements.html', {'announcements': announcements_list})





def health_bulletin(request):
    bulletins = HealthBulletin.objects.order_by('-date')
    return render(request, 'home_data/health_bulletin.html', {'bulletins': bulletins})



def medical_research(request):
    research_list = MedicalResearch.objects.order_by('-date')
    return render(request, 'home_data/medical_research.html', {'research_list': research_list})



def publications(request):
    publications = Publication.objects.order_by('-date')
    return render(request, 'home_data/publications.html', {'publications': publications})