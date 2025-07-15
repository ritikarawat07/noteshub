from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Notes
from .forms import CustomUserCreationForm, CustomUserChangeForm

# Custom admin for CustomUser
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    
    list_display = ('username', 'roll_number', 'is_teacher', 'is_student', 'is_active')
    list_filter = ('is_teacher', 'is_student', 'is_active')
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password'),
        }),
        (_('Personal info'), {
            'fields': ('roll_number',),
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_teacher', 'is_student'),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined'),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'roll_number', 'password1', 'password2', 'is_teacher', 'is_student', 'is_active'),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.is_teacher:
            form.base_fields['username'].required = True
            form.base_fields['roll_number'].required = False
        elif obj and obj.is_student:
            form.base_fields['username'].required = False
            form.base_fields['roll_number'].required = True
        return form

    list_display = ('roll_number', 'username', 'is_teacher', 'is_student', 'is_active')
    list_filter = ('is_teacher', 'is_student', 'is_active')
    search_fields = ('roll_number', 'username')
    ordering = ('roll_number',)
    filter_horizontal = ()
    readonly_fields = ('last_login', 'date_joined')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Notes)
