# noteshub/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import CustomUser, Notes
import magic    

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'roll_number', 'is_teacher', 'is_student')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'roll_number', 'is_teacher', 'is_student')

class StudentLoginForm(forms.Form):
    roll_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Roll Number',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

class TeacherLoginForm(forms.Form):
    username = forms.CharField(
        label="Username",
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'id': 'id_username'
        })
    )
    roll_number = forms.CharField(
        label="Roll Number (Optional)",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter roll number (optional)',
            'id': 'id_roll_number'
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'id_password'
        })
    )
class NotesUploadForm(forms.ModelForm):
    class Meta:
        model = Notes
        fields = ['year', 'branch', 'subject', 'chapter', 'pdf']
        widgets = {
            'year': forms.TextInput(attrs={'class': 'form-control'}),
            'branch': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'chapter': forms.TextInput(attrs={'class': 'form-control'}),
            'pdf': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_pdf(self):
        pdf = self.cleaned_data.get('pdf')
        if pdf:
            # Check file type
            file_type = magic.from_buffer(pdf.read(2048), mime=True)
            if file_type != 'application/pdf':
                raise ValidationError('Only PDF files are allowed.')

            # Reset file pointer
            pdf.seek(0)

            # Check file size (10MB max)
            if pdf.size > 10 * 1024 * 1024:
                raise ValidationError('File size must be less than 10MB.')

        return pdf
