from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import User, TrainerTraineeAssignment


class UserForm(UserCreationForm):
    """Form for creating and updating users."""
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'placeholder': 'Email Address'
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'placeholder': 'Phone Number (Optional)'
        })
    )
    role = forms.ChoiceField(
        choices=User.Role.choices,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
        })
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-emerald-600 border-slate-300 rounded focus:ring-emerald-500'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'role', 'password1', 'password2', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Username'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Password'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Confirm Password'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limit role choices based on user permissions
        if user:
            if user.is_super_admin():
                # Super admin can create all roles
                pass
            elif user.is_owner():
                # Owner can create all roles except Super Admin
                self.fields['role'].choices = [
                    choice for choice in User.Role.choices 
                    if choice[0] != User.Role.SUPER_ADMIN
                ]
            elif user.is_manager():
                # Manager can only create Trainees
                self.fields['role'].choices = [
                    (User.Role.TRAINEE, User.Role.TRAINEE.label)
                ]


class UserUpdateForm(forms.ModelForm):
    """Form for updating existing users (without password)."""
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'placeholder': 'Email Address'
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'placeholder': 'Phone Number (Optional)'
        })
    )
    role = forms.ChoiceField(
        choices=User.Role.choices,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
        })
    )
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-emerald-600 border-slate-300 rounded focus:ring-emerald-500'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'role', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Username',
                'readonly': True
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limit role choices based on user permissions
        if user:
            if user.is_super_admin():
                pass
            elif user.is_owner():
                self.fields['role'].choices = [
                    choice for choice in User.Role.choices 
                    if choice[0] != User.Role.SUPER_ADMIN
                ]
            elif user.is_manager():
                self.fields['role'].choices = [
                    (User.Role.TRAINEE, User.Role.TRAINEE.label)
                ]


class ProfileForm(forms.ModelForm):
    """Form for users to edit their own profile."""
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'placeholder': 'Email Address'
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'placeholder': 'Phone Number (Optional)'
        })
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100',
            'accept': 'image/*'
        })
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg bg-slate-100',
                'readonly': True
            }),
        }


class ProfilePasswordChangeForm(PasswordChangeForm):
    """Form for users to change their password."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'placeholder': 'Current Password'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'placeholder': 'New Password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'placeholder': 'Confirm New Password'
        })


class TrainerTraineeAssignmentForm(forms.ModelForm):
    """Form for creating and updating trainer-trainee assignments."""
    
    trainer = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.TRAINER, is_active=True),
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
        }),
        help_text="Select a trainer"
    )
    trainee = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.TRAINEE, is_active=True),
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
        }),
        help_text="Select a trainee"
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'rows': 4,
            'placeholder': 'Optional notes about this assignment...'
        })
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-emerald-600 border-slate-300 rounded focus:ring-emerald-500'
        })
    )

    class Meta:
        model = TrainerTraineeAssignment
        fields = ('trainer', 'trainee', 'notes', 'is_active')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # For new assignments, exclude already assigned trainees
        # For editing, allow the current trainee to be selected
        if self.instance and self.instance.pk:
            # When editing, exclude other active assignments but allow the current one
            assigned_trainee_ids = TrainerTraineeAssignment.objects.filter(
                is_active=True
            ).exclude(pk=self.instance.pk).values_list('trainee_id', flat=True)
            self.fields['trainee'].queryset = self.fields['trainee'].queryset.exclude(
                id__in=assigned_trainee_ids
            )
        else:
            # For new assignments, exclude all assigned trainees
            assigned_trainee_ids = TrainerTraineeAssignment.objects.filter(
                is_active=True
            ).values_list('trainee_id', flat=True)
            self.fields['trainee'].queryset = self.fields['trainee'].queryset.exclude(
                id__in=assigned_trainee_ids
            )

    def clean(self):
        cleaned_data = super().clean()
        trainer = cleaned_data.get('trainer')
        trainee = cleaned_data.get('trainee')
        
        if trainer and trainee:
            # Check if assignment already exists (excluding current instance if editing)
            existing = TrainerTraineeAssignment.objects.filter(
                trainer=trainer,
                trainee=trainee,
                is_active=True
            )
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(
                    f"This trainee is already assigned to {trainer.get_full_name() or trainer.username}."
                )
        
        return cleaned_data
