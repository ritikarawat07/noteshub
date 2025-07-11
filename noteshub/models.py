from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, roll_number, username=None, password=None, is_teacher=False, is_student=False):
        if not roll_number:
            raise ValueError("Users must have a roll number")
        
        user = self.model(
            roll_number=roll_number,
            username=username,
            is_teacher=is_teacher,
            is_student=is_student
        )
        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self, username, roll_number, password):
        user = self.create_user(
            username=username,
            roll_number=roll_number,
            password=password,
            is_teacher=True,
            is_student=False
        )
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    
    username = models.CharField(max_length=30, unique=True, null=True, blank=True)
    roll_number = models.CharField(max_length=20, unique=True, default='TEMP-0001')
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)


    objects = UserManager()

    USERNAME_FIELD = 'roll_number'
    REQUIRED_FIELDS = ['username']

    class Meta:
        app_label = 'noteshub'

    def __str__(self):
        return self.username if self.username else self.roll_number

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

# Notes Model
class Notes(models.Model):
    uploader = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    year = models.CharField(max_length=10)
    branch = models.CharField(max_length=50)
    subject = models.CharField(max_length=100)
    chapter = models.CharField(max_length=100)
    pdf = models.FileField(upload_to='noteshub/Notes_pdfs/', validators=[FileExtensionValidator(['pdf'])])
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    

    def __str__(self):
        return f"{self.subject} - {self.chapter} uploaded by {self.uploader}"
