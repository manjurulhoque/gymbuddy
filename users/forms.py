from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta, time
from .models import User, TrainerTraineeAssignment, TrainerAvailability, TrainingSession, SessionReminder


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


class BulkAttendanceForm(forms.Form):
    """Form for bulk attendance marking."""
    
    trainees = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role=User.Role.TRAINEE, is_active=True),
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'space-y-2'
        }),
        help_text="Select trainees to mark attendance for"
    )
    action = forms.ChoiceField(
        choices=[
            ('check_in', 'Check In'),
            ('check_out', 'Check Out'),
        ],
        required=True,
        widget=forms.RadioSelect(attrs={
            'class': 'space-y-2'
        }),
        help_text="Select action to perform"
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'rows': 3,
            'placeholder': 'Optional notes for all selected trainees...'
        }),
        help_text="Optional notes to add to all attendance records"
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        queryset = kwargs.pop('queryset', None)
        super().__init__(*args, **kwargs)
        
        if queryset is not None:
            self.fields['trainees'].queryset = queryset
        
        # Store user for potential use
        self.user = user
    
    def clean_trainees(self):
        """Validate that at least one trainee is selected."""
        trainees = self.cleaned_data.get('trainees')
        if not trainees:
            raise forms.ValidationError('Please select at least one trainee.')
        return trainees
    
    def clean(self):
        """Override clean to handle validation more gracefully."""
        cleaned_data = super().clean()
        
        # If trainees validation failed but we have data in POST, try to recover
        if 'trainees' not in cleaned_data and self.data:
            trainee_ids = self.data.getlist('trainees')
            if trainee_ids:
                try:
                    # Try to get the trainees directly
                    trainees = User.objects.filter(
                        id__in=[int(id) for id in trainee_ids if id.isdigit()],
                        role=User.Role.TRAINEE,
                        is_active=True
                    )
                    if trainees.exists():
                        cleaned_data['trainees'] = trainees
                    else:
                        self.add_error('trainees', 'Please select at least one valid trainee.')
                except (ValueError, TypeError):
                    self.add_error('trainees', 'Invalid trainee selection.')
        
        return cleaned_data


# Scheduling Forms

class TrainerAvailabilityForm(forms.ModelForm):
    """Form for creating and updating trainer availability."""
    
    day_of_week = forms.ChoiceField(
        choices=TrainerAvailability.DayOfWeek.choices,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
        }),
        help_text="Select day of the week"
    )
    start_time = forms.TimeField(
        required=True,
        widget=forms.TimeInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'type': 'time'
        }),
        help_text="Start time"
    )
    end_time = forms.TimeField(
        required=True,
        widget=forms.TimeInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'type': 'time'
        }),
        help_text="End time"
    )
    is_available = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-emerald-600 border-slate-300 rounded focus:ring-emerald-500'
        })
    )

    class Meta:
        model = TrainerAvailability
        fields = ('day_of_week', 'start_time', 'end_time', 'is_available')

    def __init__(self, *args, **kwargs):
        trainer = kwargs.pop('trainer', None)
        super().__init__(*args, **kwargs)
        if trainer:
            self.instance.trainer = trainer

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("End time must be after start time.")
        
        return cleaned_data


class TrainingSessionForm(forms.ModelForm):
    """Form for creating and updating training sessions."""
    
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
    session_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'type': 'date',
            'min': timezone.now().date().isoformat()
        }),
        help_text="Date of the session"
    )
    start_time = forms.TimeField(
        required=True,
        widget=forms.TimeInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'type': 'time'
        }),
        help_text="Start time"
    )
    end_time = forms.TimeField(
        required=True,
        widget=forms.TimeInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'type': 'time'
        }),
        help_text="End time"
    )
    status = forms.ChoiceField(
        choices=TrainingSession.Status.choices,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'rows': 4,
            'placeholder': 'Optional notes about this session...'
        })
    )

    class Meta:
        model = TrainingSession
        fields = ('trainer', 'trainee', 'session_date', 'start_time', 'end_time', 'status', 'notes')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If user is a trainee, limit to their assigned trainer
        if user and user.is_trainee():
            assignment = TrainerTraineeAssignment.objects.filter(
                trainee=user,
                is_active=True
            ).first()
            if assignment:
                self.fields['trainer'].queryset = User.objects.filter(id=assignment.trainer_id, is_active=True)
                self.fields['trainer'].initial = assignment.trainer
                self.fields['trainee'].initial = user
                self.fields['trainee'].widget.attrs['readonly'] = True
            else:
                self.fields['trainer'].queryset = User.objects.none()
        
        # If user is a trainer, limit to their assigned trainees
        elif user and user.is_trainer():
            trainee_ids = TrainerTraineeAssignment.objects.filter(
                trainer=user,
                is_active=True
            ).values_list('trainee_id', flat=True)
            self.fields['trainer'].initial = user
            self.fields['trainer'].widget.attrs['readonly'] = True
            self.fields['trainee'].queryset = User.objects.filter(id__in=trainee_ids, is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        session_date = cleaned_data.get('session_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        trainer = cleaned_data.get('trainer')
        
        if session_date and start_time and end_time:
            # Check if date is in the past
            if session_date < timezone.now().date():
                raise forms.ValidationError("Session date cannot be in the past.")
            
            # Check if end time is after start time
            if start_time >= end_time:
                raise forms.ValidationError("End time must be after start time.")
            
            # Check for overlapping sessions
            if trainer:
                session_datetime_start = timezone.make_aware(
                    datetime.combine(session_date, start_time)
                )
                session_datetime_end = timezone.make_aware(
                    datetime.combine(session_date, end_time)
                )
                
                overlapping = TrainingSession.objects.filter(
                    trainer=trainer,
                    session_date=session_date,
                    status__in=[TrainingSession.Status.SCHEDULED, TrainingSession.Status.CONFIRMED, TrainingSession.Status.IN_PROGRESS]
                ).exclude(
                    pk=self.instance.pk if self.instance.pk else None
                ).filter(
                    models.Q(start_time__lt=end_time, end_time__gt=start_time)
                )
                
                if overlapping.exists():
                    raise forms.ValidationError(
                        f"Trainer already has a session scheduled during this time. "
                        f"Please choose a different time slot."
                    )
        
        return cleaned_data


class SessionReminderForm(forms.ModelForm):
    """Form for creating session reminders."""
    
    reminder_type = forms.ChoiceField(
        choices=SessionReminder.ReminderType.choices,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
        })
    )
    reminder_time = forms.DateTimeField(
        required=True,
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
            'type': 'datetime-local'
        }),
        help_text="When to send the reminder"
    )

    class Meta:
        model = SessionReminder
        fields = ('reminder_type', 'reminder_time')

    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)
        if session:
            self.instance.session = session
            # Set default reminder time to 1 hour before session
            if session.session_datetime_start:
                default_time = session.session_datetime_start - timedelta(hours=1)
                self.fields['reminder_time'].initial = default_time

    def clean(self):
        cleaned_data = super().clean()
        reminder_time = cleaned_data.get('reminder_time')
        session = self.instance.session if hasattr(self.instance, 'session') else None
        
        if reminder_time and session:
            if reminder_time >= session.session_datetime_start:
                raise forms.ValidationError("Reminder time must be before the session start time.")
        
        return cleaned_data
