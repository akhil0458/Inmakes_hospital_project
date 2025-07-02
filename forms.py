from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, BaseUserCreationForm
from .models import PatientProfile, DoctorProfile, Appointment, Facility, AdminProfile, Prescription, Bill, \
    HealthEducationResource

CustomUser = get_user_model()

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    full_name = forms.CharField(max_length=150, label="Full Name")
    age = forms.IntegerField(label="Age")
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    phone = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ['full_name', 'age', 'gender', 'phone', 'address']


class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = ['full_name', 'age', 'gender', 'phone', 'address', 'specialization', 'available_days']



class AdminCreationForm(forms.ModelForm):

    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


    full_name = forms.CharField(max_length=100)
    age = forms.IntegerField()
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female')])
    phone = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password',
                  'full_name', 'age', 'gender', 'phone', 'address']



class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'time']


class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = ['name', 'location', 'departments', 'resources']


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'is_doctor', 'is_patient')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'is_doctor', 'is_patient')


class AdminUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    is_doctor = forms.BooleanField(required=False, label='Doctor Role')
    is_patient = forms.BooleanField(required=False, label='Patient Role')
    is_admin = forms.BooleanField(required=False, label='Admin Role')

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'is_doctor', 'is_patient', 'is_admin']

    def clean_password2(self):
        pw1 = self.cleaned_data.get("password1")
        pw2 = self.cleaned_data.get("password2")
        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError("Passwords don't match.")
        return pw2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user





User = get_user_model()

class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')





class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['patient', 'medication_name', 'dosage', 'frequency', 'duration', 'notes']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'medication_name': forms.TextInput(attrs={'class': 'form-control'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control'}),
            'frequency': forms.TextInput(attrs={'class': 'form-control'}),
            'duration': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }



class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ['full_name', 'age', 'gender', 'phone', 'address']
        
        
        
class BillingForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['patient', 'amount', 'description']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super(BillingForm, self).__init__(*args, **kwargs)
        self.fields['patient'].label = "Select Patient"
        self.fields['amount'].label = "Amount (₹)"
        self.fields['description'].label = "Description"

    def create_razorpay_order(self, razorpay=None):
        """
        Call this method *after* validating the form to generate a Razorpay order.
        """
        amount = int(self.cleaned_data['amount']) * 100  # Convert rupees to paisa
        client = razorpay.Client(auth=("YOUR_RAZORPAY_KEY_ID", "YOUR_RAZORPAY_KEY_SECRET"))

        order_data = {
            'amount': amount,
            'currency': 'INR',
            'payment_capture': '1'
        }

        return client.order.create(data=order_data)





class HealthEducationResourceForm(forms.ModelForm):
    class Meta:
        model = HealthEducationResource
        fields = ['title', 'description', 'link']