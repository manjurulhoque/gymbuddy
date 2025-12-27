from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import TemplateView, View, ListView, CreateView, UpdateView, DeleteView, FormView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.db import models
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Q, Avg, Sum
from .models import User, TrainerTraineeAssignment, Attendance, TrainerAvailability, TrainingSession, SessionReminder
from .forms import (
    UserForm, UserUpdateForm, ProfileForm, ProfilePasswordChangeForm, 
    TrainerTraineeAssignmentForm, BulkAttendanceForm,
    TrainerAvailabilityForm, TrainingSessionForm, SessionReminderForm
)
from .mixins import StaffOrAboveRequiredMixin, SuperAdminOrOwnerRequiredMixin


class LoginView(TemplateView):
    """
    Custom login view with role-based authentication using class-based view.
    """
    template_name = 'users/login.html'

    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users to dashboard."""
        if request.user.is_authenticated:
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Handle POST request for login."""
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Handle "Remember Me" functionality
                    if not remember_me:
                        # Session expires when browser closes
                        request.session.set_expiry(0)
                    else:
                        # Session expires after 2 weeks
                        request.session.set_expiry(1209600)
                    
                    messages.success(
                        request, 
                        f'Welcome back, {user.get_full_name() or user.username}!'
                    )
                    
                    # Redirect based on user role
                    next_url = request.GET.get('next', 'core:dashboard')
                    return redirect(next_url)
                else:
                    messages.error(
                        request, 
                        'Your account has been disabled. Please contact an administrator.'
                    )
            else:
                messages.error(
                    request, 
                    'Invalid username or password. Please try again.'
                )
        else:
            messages.error(
                request, 
                'Please provide both username and password.'
            )
        
        # Re-render the form with errors
        return self.get(request, *args, **kwargs)


class LogoutView(View):
    """
    Custom logout view using class-based view.
    """
    
    @method_decorator(require_http_methods(["POST"]))
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Handle POST request for logout."""
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('core:home')


class UserListView(StaffOrAboveRequiredMixin, ListView):
    """List view for users with pagination."""
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    paginate_by = 15
    login_url = "users:login"

    def get_queryset(self):
        queryset = User.objects.all()
        current_user = self.request.user
        search_query = self.request.GET.get('search', '')
        role_filter = self.request.GET.get('role', '')
        status_filter = self.request.GET.get('status', '')
        
        # Filter based on user role
        if current_user.is_manager():
            # Managers can only see Trainees
            queryset = queryset.filter(role=User.Role.TRAINEE)
        elif current_user.is_owner():
            # Owners can see Trainees and Managers
            queryset = queryset.filter(role__in=[User.Role.TRAINEE, User.Role.MANAGER])
        # Super Admin can see all users
        
        # Role filter
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        # Status filter
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Search functionality
        if search_query:
            queryset = queryset.filter(
                models.Q(username__icontains=search_query) |
                models.Q(first_name__icontains=search_query) |
                models.Q(last_name__icontains=search_query) |
                models.Q(email__icontains=search_query) |
                models.Q(phone_number__icontains=search_query)
            )
        
        return queryset.order_by('-date_joined')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['role_filter'] = self.request.GET.get('role', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['form'] = UserForm(user=self.request.user)
        
        # Get available roles based on current user
        current_user = self.request.user
        if current_user.is_super_admin():
            context['available_roles'] = User.Role.choices
        elif current_user.is_owner():
            context['available_roles'] = [
                choice for choice in User.Role.choices 
                if choice[0] != User.Role.SUPER_ADMIN
            ]
        elif current_user.is_manager():
            context['available_roles'] = [(User.Role.TRAINEE, User.Role.TRAINEE.label)]
        else:
            context['available_roles'] = []
        
        return context


class UserCreateView(StaffOrAboveRequiredMixin, CreateView):
    """Create view for users."""
    model = User
    form_class = UserForm
    template_name = "users/user_create.html"
    login_url = "users:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, f'User {user.get_full_name() or user.username} created successfully!')
        return redirect('users:user_list')

    def get_success_url(self):
        return reverse_lazy('users:user_list')


class UserUpdateView(StaffOrAboveRequiredMixin, UpdateView):
    """Update view for users."""
    model = User
    form_class = UserUpdateForm
    template_name = "users/user_update.html"
    login_url = "users:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, f'User {user.get_full_name() or user.username} updated successfully!')
        return redirect('users:user_list')

    def get_success_url(self):
        return reverse_lazy('users:user_list')


class UserDeleteView(SuperAdminOrOwnerRequiredMixin, DeleteView):
    """Delete view for users (only Super Admin and Owner)."""
    model = User
    template_name = "users/user_confirm_delete.html"
    login_url = "users:login"

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        username = user.get_full_name() or user.username
        
        # Prevent self-deletion
        if user == request.user:
            messages.error(request, 'You cannot delete your own account.')
            return redirect('users:user_list')
        
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
        return redirect('users:user_list')

    def get_success_url(self):
        return reverse_lazy('users:user_list')


class ProfileView(LoginRequiredMixin, TemplateView):
    """View to display user's own profile."""
    template_name = "users/profile.html"
    login_url = "users:login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """View for users to edit their own profile."""
    model = User
    form_class = ProfileForm
    template_name = "users/profile_edit.html"
    login_url = "users:login"

    def get_object(self):
        """Return the current user."""
        return self.request.user

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, 'Your profile has been updated successfully!')
        return redirect('users:profile')

    def get_success_url(self):
        return reverse_lazy('users:profile')


class ProfilePasswordChangeView(LoginRequiredMixin, FormView):
    """View for users to change their password."""
    form_class = ProfilePasswordChangeForm
    template_name = "users/profile_password_change.html"
    login_url = "users:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, 'Your password has been changed successfully!')
        return redirect('users:profile')

    def get_success_url(self):
        return reverse_lazy('users:profile')


# Trainer-Trainee Assignment Views

class AssignmentListView(StaffOrAboveRequiredMixin, ListView):
    """List view for trainer-trainee assignments."""
    model = TrainerTraineeAssignment
    template_name = "users/assignment_list.html"
    context_object_name = "assignments"
    paginate_by = 20
    login_url = "users:login"

    def get_queryset(self):
        queryset = TrainerTraineeAssignment.objects.select_related('trainer', 'trainee', 'assigned_by').all()
        
        # Filter by active status
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                models.Q(trainer__username__icontains=search_query) |
                models.Q(trainer__first_name__icontains=search_query) |
                models.Q(trainer__last_name__icontains=search_query) |
                models.Q(trainee__username__icontains=search_query) |
                models.Q(trainee__first_name__icontains=search_query) |
                models.Q(trainee__last_name__icontains=search_query)
            )
        
        return queryset.order_by('-assigned_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class AssignmentCreateView(StaffOrAboveRequiredMixin, CreateView):
    """Create view for trainer-trainee assignments."""
    model = TrainerTraineeAssignment
    form_class = TrainerTraineeAssignmentForm
    template_name = "users/assignment_form.html"
    login_url = "users:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        assignment = form.save(commit=False)
        assignment.assigned_by = self.request.user
        assignment.save()
        messages.success(
            self.request,
            f'Successfully assigned {assignment.trainee.get_full_name() or assignment.trainee.username} to {assignment.trainer.get_full_name() or assignment.trainer.username}!'
        )
        return redirect('users:assignment_list')

    def get_success_url(self):
        return reverse_lazy('users:assignment_list')


class AssignmentUpdateView(StaffOrAboveRequiredMixin, UpdateView):
    """Update view for trainer-trainee assignments."""
    model = TrainerTraineeAssignment
    form_class = TrainerTraineeAssignmentForm
    template_name = "users/assignment_form.html"
    login_url = "users:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        assignment = form.save()
        messages.success(
            self.request,
            f'Assignment updated successfully!'
        )
        return redirect('users:assignment_list')

    def get_success_url(self):
        return reverse_lazy('users:assignment_list')


class AssignmentDeleteView(StaffOrAboveRequiredMixin, DeleteView):
    """Delete view for trainer-trainee assignments."""
    model = TrainerTraineeAssignment
    template_name = "users/assignment_confirm_delete.html"
    login_url = "users:login"

    def delete(self, request, *args, **kwargs):
        assignment = self.get_object()
        assignment.delete()
        messages.success(request, 'Assignment deleted successfully!')
        return redirect('users:assignment_list')

    def get_success_url(self):
        return reverse_lazy('users:assignment_list')


class TrainerTraineesView(LoginRequiredMixin, TemplateView):
    """View for trainers to see their assigned trainees."""
    template_name = "users/trainer_trainees.html"
    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_trainer():
            messages.error(request, 'You must be a trainer to access this page.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignments = TrainerTraineeAssignment.objects.filter(
            trainer=self.request.user,
            is_active=True
        ).select_related('trainee').order_by('-assigned_at')
        context['assignments'] = assignments
        context['trainees'] = [assignment.trainee for assignment in assignments]
        return context


class TraineeTrainerView(LoginRequiredMixin, TemplateView):
    """View for trainees to see their assigned trainer."""
    template_name = "users/trainee_trainer.html"
    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_trainee():
            messages.error(request, 'You must be a trainee to access this page.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = TrainerTraineeAssignment.objects.filter(
            trainee=self.request.user,
            is_active=True
        ).select_related('trainer', 'assigned_by').first()
        context['assignment'] = assignment
        context['trainer'] = assignment.trainer if assignment else None
        return context


# Attendance Views

class CheckInView(LoginRequiredMixin, View):
    """View for trainees to check in."""
    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_trainee():
            messages.error(request, 'Only trainees can check in.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Check if already checked in (has an active attendance without check_out)
        active_attendance = Attendance.objects.filter(
            trainee=request.user,
            check_out__isnull=True
        ).first()

        if active_attendance:
            messages.warning(request, 'You are already checked in. Please check out first.')
            return redirect('users:attendance_check_in')

        # Create new attendance record
        attendance = Attendance.objects.create(
            trainee=request.user,
            check_in=timezone.now(),
            marked_by=None  # Self check-in
        )
        messages.success(request, f'Checked in successfully at {attendance.check_in.strftime("%H:%M:%S")}')
        return redirect('users:attendance_check_in')


class CheckOutView(LoginRequiredMixin, View):
    """View for trainees to check out."""
    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_trainee():
            messages.error(request, 'Only trainees can check out.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Find active attendance
        attendance = Attendance.objects.filter(
            trainee=request.user,
            check_out__isnull=True
        ).first()

        if not attendance:
            messages.warning(request, 'You are not currently checked in.')
            return redirect('users:attendance_check_in')

        # Update check-out time
        attendance.check_out = timezone.now()
        attendance.save()

        duration = attendance.duration
        hours = duration // 60 if duration else 0
        minutes = duration % 60 if duration else 0
        messages.success(
            request,
            f'Checked out successfully. Duration: {hours}h {minutes}m'
        )
        return redirect('users:attendance_check_in')


class AttendanceCheckInView(LoginRequiredMixin, TemplateView):
    """View to display check-in/check-out interface."""
    template_name = "users/attendance_check_in.html"
    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_trainee():
            messages.error(request, 'Only trainees can access this page.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get current active attendance
        active_attendance = Attendance.objects.filter(
            trainee=self.request.user,
            check_out__isnull=True
        ).first()
        context['active_attendance'] = active_attendance
        context['is_checked_in'] = active_attendance is not None
        
        # Get today's attendance summary
        today = timezone.now().date()
        today_attendance = Attendance.objects.filter(
            trainee=self.request.user,
            check_in__date=today
        ).first()
        context['today_attendance'] = today_attendance
        
        return context


class AttendanceHistoryView(LoginRequiredMixin, ListView):
    """View to display attendance history."""
    model = Attendance
    template_name = "users/attendance_history.html"
    context_object_name = "attendances"
    paginate_by = 20
    login_url = "users:login"

    def get_queryset(self):
        user = self.request.user
        
        if user.is_trainee():
            # Trainees see their own attendance
            queryset = Attendance.objects.filter(trainee=user)
        elif user.is_trainer():
            # Trainers see attendance of their assigned trainees
            trainee_ids = TrainerTraineeAssignment.objects.filter(
                trainer=user,
                is_active=True
            ).values_list('trainee_id', flat=True)
            queryset = Attendance.objects.filter(trainee_id__in=trainee_ids)
        else:
            # Staff/Admin see all attendance
            queryset = Attendance.objects.all()

        # Filter by date range if provided
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            queryset = queryset.filter(check_in__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(check_in__date__lte=date_to)

        # Search by trainee name
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(trainee__username__icontains=search_query) |
                Q(trainee__first_name__icontains=search_query) |
                Q(trainee__last_name__icontains=search_query)
            )

        return queryset.select_related('trainee', 'marked_by').order_by('-check_in')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['is_trainer'] = self.request.user.is_trainer()
        context['is_trainee'] = self.request.user.is_trainee()
        return context


class AttendanceStatisticsView(LoginRequiredMixin, TemplateView):
    """View to display attendance statistics dashboard."""
    template_name = "users/attendance_statistics.html"
    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_trainer() or request.user.is_staff_or_above()):
            messages.error(request, 'You do not have permission to view statistics.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        this_week_start = today - timedelta(days=today.weekday())
        this_month_start = today.replace(day=1)

        # Get queryset based on user role
        if user.is_trainee():
            attendances = Attendance.objects.filter(trainee=user)
        elif user.is_trainer():
            trainee_ids = TrainerTraineeAssignment.objects.filter(
                trainer=user,
                is_active=True
            ).values_list('trainee_id', flat=True)
            attendances = Attendance.objects.filter(trainee_id__in=trainee_ids)
        else:
            attendances = Attendance.objects.all()

        # Today's statistics
        today_attendances = attendances.filter(check_in__date=today)
        context['today_count'] = today_attendances.count()
        context['today_checked_in'] = today_attendances.filter(check_out__isnull=True).count()

        # This week's statistics
        week_attendances = attendances.filter(check_in__date__gte=this_week_start)
        context['week_count'] = week_attendances.count()
        # Calculate average duration for completed sessions
        completed_week = week_attendances.exclude(check_out__isnull=True)
        if completed_week.exists():
            total_minutes = sum(att.duration for att in completed_week if att.duration)
            context['week_avg_duration'] = total_minutes / completed_week.count() if completed_week.count() > 0 else 0
        else:
            context['week_avg_duration'] = 0

        # This month's statistics
        month_attendances = attendances.filter(check_in__date__gte=this_month_start)
        context['month_count'] = month_attendances.count()

        # Total statistics
        context['total_count'] = attendances.count()
        context['total_checked_in'] = attendances.filter(check_out__isnull=True).count()

        # Recent attendances (last 10)
        context['recent_attendances'] = attendances.select_related('trainee', 'marked_by')[:10]

        # Daily attendance for the last 7 days
        last_7_days = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            count = attendances.filter(check_in__date=date).count()
            last_7_days.append({'date': date, 'count': count})
        context['last_7_days'] = last_7_days

        # Top trainees (if trainer or staff)
        if user.is_trainer() or user.is_staff_or_above():
            top_trainees = attendances.values('trainee__username', 'trainee__first_name', 'trainee__last_name').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            context['top_trainees'] = top_trainees

        return context


class TrainerMarkAttendanceView(LoginRequiredMixin, View):
    """View for trainers and staff to mark attendance for trainees."""
    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_trainer() or request.user.is_staff_or_above()):
            messages.error(request, 'You do not have permission to mark attendance.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Staff users can see all trainees, trainers see only assigned ones
        if user.is_staff_or_above():
            # Get all trainees based on staff level
            if user.is_manager():
                trainees = User.objects.filter(role=User.Role.TRAINEE, is_active=True)
            elif user.is_owner():
                trainees = User.objects.filter(role__in=[User.Role.TRAINEE, User.Role.MANAGER], is_active=True)
            else:  # Super Admin
                trainees = User.objects.filter(role=User.Role.TRAINEE, is_active=True)
            trainees = list(trainees)
        else:
            # Get trainer's assigned trainees
            assignments = TrainerTraineeAssignment.objects.filter(
                trainer=request.user,
                is_active=True
            ).select_related('trainee')
            trainees = [assignment.trainee for assignment in assignments]
        
        # Get today's attendance for these trainees
        today = timezone.now().date()
        today_attendances = Attendance.objects.filter(
            trainee__in=trainees,
            check_in__date=today
        ).select_related('trainee')
        
        attendance_dict = {att.trainee_id: att for att in today_attendances}
        
        # Create list of tuples (trainee, attendance) for easier template access
        trainee_attendance_list = []
        for trainee in trainees:
            attendance = attendance_dict.get(trainee.id)
            trainee_attendance_list.append((trainee, attendance))
        
        context = {
            'trainee_attendance_list': trainee_attendance_list,
            'today': today,
            'is_staff': user.is_staff_or_above(),
        }
        return render(request, 'users/trainer_mark_attendance.html', context)

    def post(self, request, *args, **kwargs):
        trainee_id = request.POST.get('trainee_id')
        action = request.POST.get('action')  # 'check_in' or 'check_out'
        notes = request.POST.get('notes', '')

        if not trainee_id or not action:
            messages.error(request, 'Invalid request.')
            return redirect('users:trainer_mark_attendance')

        user = request.user
        
        # Staff users can mark attendance for any trainee, trainers only for assigned ones
        if user.is_staff_or_above():
            try:
                trainee = User.objects.get(id=trainee_id, role=User.Role.TRAINEE)
            except User.DoesNotExist:
                messages.error(request, 'Trainee not found.')
                return redirect('users:trainer_mark_attendance')
        else:
            # Verify trainee is assigned to this trainer
            assignment = TrainerTraineeAssignment.objects.filter(
                trainer=request.user,
                trainee_id=trainee_id,
                is_active=True
            ).first()

            if not assignment:
                messages.error(request, 'Trainee is not assigned to you.')
                return redirect('users:trainer_mark_attendance')

            trainee = assignment.trainee

        if action == 'check_in':
            # Check if already checked in today
            today = timezone.now().date()
            existing = Attendance.objects.filter(
                trainee=trainee,
                check_in__date=today,
                check_out__isnull=True
            ).first()

            if existing:
                messages.warning(request, f'{trainee.get_full_name() or trainee.username} is already checked in.')
            else:
                Attendance.objects.create(
                    trainee=trainee,
                    check_in=timezone.now(),
                    marked_by=request.user,
                    notes=notes
                )
                messages.success(request, f'Checked in {trainee.get_full_name() or trainee.username} successfully.')

        elif action == 'check_out':
            # Find active attendance
            attendance = Attendance.objects.filter(
                trainee=trainee,
                check_out__isnull=True
            ).order_by('-check_in').first()

            if not attendance:
                messages.warning(request, f'{trainee.get_full_name() or trainee.username} is not checked in.')
            else:
                attendance.check_out = timezone.now()
                if notes:
                    attendance.notes = (attendance.notes + '\n' + notes) if attendance.notes else notes
                attendance.save()
                messages.success(request, f'Checked out {trainee.get_full_name() or trainee.username} successfully.')

        return redirect('users:trainer_mark_attendance')


class BulkAttendanceMarkView(LoginRequiredMixin, FormView):
    """View for trainers and staff to mark attendance for multiple trainees at once."""
    form_class = BulkAttendanceForm
    template_name = "users/bulk_attendance_mark.html"
    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_trainer() or request.user.is_staff_or_above()):
            messages.error(request, 'You do not have permission to mark attendance.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.request.user
        
        # Get available trainees based on user role
        if user.is_staff_or_above():
            if user.is_manager():
                trainees = User.objects.filter(role=User.Role.TRAINEE, is_active=True)
            elif user.is_owner():
                trainees = User.objects.filter(role=User.Role.TRAINEE, is_active=True)
            else:  # Super Admin
                trainees = User.objects.filter(role=User.Role.TRAINEE, is_active=True)
        else:
            # Get trainer's assigned trainees
            assignments = TrainerTraineeAssignment.objects.filter(
                trainer=user,
                is_active=True
            ).select_related('trainee')
            trainee_ids = [assignment.trainee_id for assignment in assignments]
            trainees = User.objects.filter(id__in=trainee_ids, is_active=True)
        
        kwargs['queryset'] = trainees
        kwargs['user'] = user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get available trainees for display
        if user.is_staff_or_above():
            if user.is_manager():
                trainees = User.objects.filter(role=User.Role.TRAINEE, is_active=True)
            elif user.is_owner():
                trainees = User.objects.filter(role=User.Role.TRAINEE, is_active=True)
            else:  # Super Admin
                trainees = User.objects.filter(role=User.Role.TRAINEE, is_active=True)
        else:
            assignments = TrainerTraineeAssignment.objects.filter(
                trainer=user,
                is_active=True
            ).select_related('trainee')
            trainee_ids = [assignment.trainee_id for assignment in assignments]
            trainees = User.objects.filter(id__in=trainee_ids, is_active=True)
        
        # Get today's attendance status for each trainee
        today = timezone.now().date()
        today_attendances = Attendance.objects.filter(
            trainee__in=trainees,
            check_in__date=today
        ).select_related('trainee')
        
        attendance_dict = {}
        for att in today_attendances:
            if att.check_out is None:
                attendance_dict[att.trainee_id] = {'status': 'checked_in', 'attendance': att}
            else:
                attendance_dict[att.trainee_id] = {'status': 'checked_out', 'attendance': att}
        
        trainee_list = []
        for trainee in trainees:
            status_info = attendance_dict.get(trainee.id, {'status': 'not_checked_in', 'attendance': None})
            trainee_list.append({
                'trainee': trainee,
                'status': status_info['status'],
                'attendance': status_info['attendance']
            })
        
        context['trainee_list'] = trainee_list
        context['today'] = today
        context['is_staff'] = user.is_staff_or_above()
        return context

    def form_valid(self, form):
        trainees = form.cleaned_data['trainees']
        action = form.cleaned_data['action']
        notes = form.cleaned_data.get('notes', '')
        
        user = self.request.user
        today = timezone.now().date()
        success_count = 0
        warning_count = 0
        error_messages = []
        
        for trainee in trainees:
            # Verify permission for trainers
            if not user.is_staff_or_above():
                assignment = TrainerTraineeAssignment.objects.filter(
                    trainer=user,
                    trainee=trainee,
                    is_active=True
                ).first()
                if not assignment:
                    error_messages.append(f"{trainee.get_full_name() or trainee.username} is not assigned to you.")
                    continue
            
            if action == 'check_in':
                # Check if already checked in today
                existing = Attendance.objects.filter(
                    trainee=trainee,
                    check_in__date=today,
                    check_out__isnull=True
                ).first()
                
                if existing:
                    warning_count += 1
                    error_messages.append(f"{trainee.get_full_name() or trainee.username} is already checked in.")
                else:
                    Attendance.objects.create(
                        trainee=trainee,
                        check_in=timezone.now(),
                        marked_by=user,
                        notes=notes
                    )
                    success_count += 1
            
            elif action == 'check_out':
                # Find active attendance
                attendance = Attendance.objects.filter(
                    trainee=trainee,
                    check_out__isnull=True
                ).order_by('-check_in').first()
                
                if not attendance:
                    warning_count += 1
                    error_messages.append(f"{trainee.get_full_name() or trainee.username} is not checked in.")
                else:
                    attendance.check_out = timezone.now()
                    if notes:
                        attendance.notes = (attendance.notes + '\n' + notes) if attendance.notes else notes
                    attendance.save()
                    success_count += 1
        
        # Display summary messages
        if success_count > 0:
            messages.success(
                self.request,
                f'Successfully {action.replace("_", " ")} {success_count} trainee(s).'
            )
        
        if warning_count > 0:
            messages.warning(
                self.request,
                f'{warning_count} trainee(s) could not be processed. See details below.'
            )
        
        if error_messages:
            for msg in error_messages[:10]:  # Limit to first 10 messages
                messages.info(self.request, msg)
            if len(error_messages) > 10:
                messages.info(self.request, f'... and {len(error_messages) - 10} more messages.')
        
        return redirect('users:bulk_attendance_mark')


# Scheduling Views

class TrainerAvailabilityListView(LoginRequiredMixin, ListView):
    """List view for trainer availability."""
    model = TrainerAvailability
    template_name = "users/trainer_availability_list.html"
    context_object_name = "availabilities"
    paginate_by = 20
    login_url = "users:login"

    def get_queryset(self):
        user = self.request.user
        
        if user.is_trainer():
            # Trainers see their own availability
            queryset = TrainerAvailability.objects.filter(trainer=user)
        elif user.is_trainee():
            # Trainees see their assigned trainer's availability
            assignment = TrainerTraineeAssignment.objects.filter(
                trainee=user,
                is_active=True
            ).first()
            if assignment:
                queryset = TrainerAvailability.objects.filter(
                    trainer=assignment.trainer,
                    is_available=True
                )
            else:
                queryset = TrainerAvailability.objects.none()
        else:
            # Staff see all availability
            queryset = TrainerAvailability.objects.all()
        
        # Filter by trainer if provided
        trainer_id = self.request.GET.get('trainer')
        if trainer_id:
            queryset = queryset.filter(trainer_id=trainer_id)
        
        # Filter by day of week if provided
        day_of_week = self.request.GET.get('day_of_week')
        if day_of_week:
            queryset = queryset.filter(day_of_week=day_of_week)
        
        return queryset.select_related('trainer').order_by('trainer', 'day_of_week', 'start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trainer_filter'] = self.request.GET.get('trainer', '')
        context['day_filter'] = self.request.GET.get('day_of_week', '')
        context['is_trainer'] = self.request.user.is_trainer()
        context['is_trainee'] = self.request.user.is_trainee()
        
        # Get available trainers for filter
        if self.request.user.is_staff_or_above():
            context['trainers'] = User.objects.filter(role=User.Role.TRAINER, is_active=True)
        
        return context


class TrainerAvailabilityCreateView(LoginRequiredMixin, CreateView):
    """Create view for trainer availability."""
    model = TrainerAvailability
    form_class = TrainerAvailabilityForm
    template_name = "users/trainer_availability_form.html"
    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_trainer():
            messages.error(request, 'Only trainers can manage their availability.')
            return redirect('users:trainer_availability_list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['trainer'] = self.request.user
        return kwargs

    def form_valid(self, form):
        availability = form.save(commit=False)
        availability.trainer = self.request.user
        availability.save()
        messages.success(self.request, 'Availability slot created successfully!')
        return redirect('users:trainer_availability_list')

    def get_success_url(self):
        return reverse_lazy('users:trainer_availability_list')


class TrainerAvailabilityUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for trainer availability."""
    model = TrainerAvailability
    form_class = TrainerAvailabilityForm
    template_name = "users/trainer_availability_form.html"
    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        availability = self.get_object()
        if not request.user.is_trainer() or availability.trainer != request.user:
            messages.error(request, 'You can only edit your own availability.')
            return redirect('users:trainer_availability_list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['trainer'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Availability updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('users:trainer_availability_list')


class TrainerAvailabilityDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for trainer availability."""
    model = TrainerAvailability
    template_name = "users/trainer_availability_confirm_delete.html"
    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        availability = self.get_object()
        if not request.user.is_trainer() or availability.trainer != request.user:
            messages.error(request, 'You can only delete your own availability.')
            return redirect('users:trainer_availability_list')
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        availability = self.get_object()
        availability.delete()
        messages.success(request, 'Availability slot deleted successfully!')
        return redirect('users:trainer_availability_list')

    def get_success_url(self):
        return reverse_lazy('users:trainer_availability_list')


class TrainingSessionListView(LoginRequiredMixin, ListView):
    """List view for training sessions."""
    model = TrainingSession
    template_name = "users/training_session_list.html"
    context_object_name = "sessions"
    paginate_by = 20
    login_url = "users:login"

    def get_queryset(self):
        user = self.request.user
        
        if user.is_trainee():
            # Trainees see their own sessions
            queryset = TrainingSession.objects.filter(trainee=user)
        elif user.is_trainer():
            # Trainers see sessions with their assigned trainees
            queryset = TrainingSession.objects.filter(trainer=user)
        else:
            # Staff see all sessions
            queryset = TrainingSession.objects.all()
        
        # Filter by status
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(session_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(session_date__lte=date_to)
        
        return queryset.select_related('trainer', 'trainee', 'created_by').order_by('-session_date', '-start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['is_trainer'] = self.request.user.is_trainer()
        context['is_trainee'] = self.request.user.is_trainee()
        return context


class TrainingSessionCreateView(LoginRequiredMixin, CreateView):
    """Create view for training sessions."""
    model = TrainingSession
    form_class = TrainingSessionForm
    template_name = "users/training_session_form.html"
    login_url = "users:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        session = form.save(commit=False)
        session.created_by = self.request.user
        session.save()
        messages.success(self.request, 'Training session booked successfully!')
        return redirect('users:training_session_list')

    def get_success_url(self):
        return reverse_lazy('users:training_session_list')


class TrainingSessionUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for training sessions."""
    model = TrainingSession
    form_class = TrainingSessionForm
    template_name = "users/training_session_form.html"
    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        session = self.get_object()
        # Allow trainers, trainees, and staff to update
        if not (request.user == session.trainer or request.user == session.trainee or request.user.is_staff_or_above()):
            messages.error(request, 'You do not have permission to edit this session.')
            return redirect('users:training_session_list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Training session updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('users:training_session_list')


class TrainingSessionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for training sessions."""
    model = TrainingSession
    template_name = "users/training_session_confirm_delete.html"
    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        session = self.get_object()
        # Allow trainers, trainees, and staff to delete
        if not (request.user == session.trainer or request.user == session.trainee or request.user.is_staff_or_above()):
            messages.error(request, 'You do not have permission to delete this session.')
            return redirect('users:training_session_list')
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        session = self.get_object()
        session.delete()
        messages.success(request, 'Training session deleted successfully!')
        return redirect('users:training_session_list')

    def get_success_url(self):
        return reverse_lazy('users:training_session_list')


class TrainingSessionCancelView(LoginRequiredMixin, View):
    """View to cancel a training session."""
    login_url = "users:login"

    def post(self, request, *args, **kwargs):
        session_id = request.POST.get('session_id')
        reason = request.POST.get('reason', '')
        
        try:
            session = TrainingSession.objects.get(pk=session_id)
        except TrainingSession.DoesNotExist:
            messages.error(request, 'Session not found.')
            return redirect('users:training_session_list')
        
        # Check permissions
        if not (request.user == session.trainer or request.user == session.trainee or request.user.is_staff_or_above()):
            messages.error(request, 'You do not have permission to cancel this session.')
            return redirect('users:training_session_list')
        
        # Cancel the session
        session.status = TrainingSession.Status.CANCELLED
        session.cancelled_at = timezone.now()
        session.cancelled_by = request.user
        session.cancellation_reason = reason
        session.save()
        
        messages.success(request, 'Training session cancelled successfully!')
        return redirect('users:training_session_list')


class CalendarView(LoginRequiredMixin, TemplateView):
    """Calendar view for training sessions."""
    template_name = "users/calendar.html"
    login_url = "users:login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get date range (current month by default)
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))
        
        # Get sessions for the month
        if user.is_trainee():
            sessions = TrainingSession.objects.filter(
                trainee=user,
                session_date__year=year,
                session_date__month=month
            )
        elif user.is_trainer():
            sessions = TrainingSession.objects.filter(
                trainer=user,
                session_date__year=year,
                session_date__month=month
            )
        else:
            sessions = TrainingSession.objects.filter(
                session_date__year=year,
                session_date__month=month
            )
        
        # Organize sessions by date
        sessions_by_date = {}
        for session in sessions.select_related('trainer', 'trainee'):
            date_key = session.session_date.isoformat()
            if date_key not in sessions_by_date:
                sessions_by_date[date_key] = []
            sessions_by_date[date_key].append(session)
        
        # Generate calendar days
        from calendar import monthcalendar
        import calendar
        cal = monthcalendar(year, month)
        calendar_days = []
        for week in cal:
            week_days = []
            for day in week:
                if day == 0:
                    week_days.append(None)
                else:
                    date_key = f"{year}-{month:02d}-{day:02d}"
                    day_sessions = sessions_by_date.get(date_key, [])
                    week_days.append({
                        'day': day,
                        'date': date_key,
                        'sessions': day_sessions,
                        'is_today': date_key == current_date.isoformat()
                    })
            calendar_days.append(week_days)
        
        context['calendar_days'] = calendar_days
        context['month_name'] = calendar.month_name[month]
        
        context['sessions_by_date'] = sessions_by_date
        context['year'] = year
        context['month'] = month
        context['current_date'] = timezone.now().date()
        
        # Calculate previous and next month
        if month == 1:
            prev_month = 12
            prev_year = year - 1
        else:
            prev_month = month - 1
            prev_year = year
        
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        
        context['prev_month'] = prev_month
        context['prev_year'] = prev_year
        context['next_month'] = next_month
        context['next_year'] = next_year
        
        return context


class SessionReminderListView(LoginRequiredMixin, ListView):
    """List view for session reminders."""
    model = SessionReminder
    template_name = "users/session_reminder_list.html"
    context_object_name = "reminders"
    paginate_by = 20
    login_url = "users:login"

    def get_queryset(self):
        user = self.request.user
        
        if user.is_trainee():
            # Trainees see reminders for their sessions
            session_ids = TrainingSession.objects.filter(trainee=user).values_list('id', flat=True)
            queryset = SessionReminder.objects.filter(session_id__in=session_ids)
        elif user.is_trainer():
            # Trainers see reminders for their sessions
            session_ids = TrainingSession.objects.filter(trainer=user).values_list('id', flat=True)
            queryset = SessionReminder.objects.filter(session_id__in=session_ids)
        else:
            # Staff see all reminders
            queryset = SessionReminder.objects.all()
        
        return queryset.select_related('session', 'session__trainer', 'session__trainee').order_by('reminder_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_trainer'] = self.request.user.is_trainer()
        context['is_trainee'] = self.request.user.is_trainee()
        return context


class SessionReminderCreateView(LoginRequiredMixin, CreateView):
    """Create view for session reminders."""
    model = SessionReminder
    form_class = SessionReminderForm
    template_name = "users/session_reminder_form.html"
    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        session_id = request.GET.get('session')
        if not session_id:
            messages.error(request, 'Please select a session.')
            return redirect('users:training_session_list')
        
        try:
            session = TrainingSession.objects.get(pk=session_id)
        except TrainingSession.DoesNotExist:
            messages.error(request, 'Session not found.')
            return redirect('users:training_session_list')
        
        # Check permissions
        if not (request.user == session.trainer or request.user == session.trainee or request.user.is_staff_or_above()):
            messages.error(request, 'You do not have permission to create reminders for this session.')
            return redirect('users:training_session_list')
        
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        session_id = self.request.GET.get('session')
        session = TrainingSession.objects.get(pk=session_id)
        kwargs['session'] = session
        return kwargs

    def form_valid(self, form):
        reminder = form.save(commit=False)
        session_id = self.request.GET.get('session')
        reminder.session = TrainingSession.objects.get(pk=session_id)
        reminder.save()
        messages.success(self.request, 'Reminder created successfully!')
        return redirect('users:session_reminder_list')

    def get_success_url(self):
        return reverse_lazy('users:session_reminder_list')


class SessionReminderDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for session reminders."""
    model = SessionReminder
    template_name = "users/session_reminder_confirm_delete.html"
    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        reminder = self.get_object()
        session = reminder.session
        # Check permissions
        if not (request.user == session.trainer or request.user == session.trainee or request.user.is_staff_or_above()):
            messages.error(request, 'You do not have permission to delete this reminder.')
            return redirect('users:session_reminder_list')
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        reminder = self.get_object()
        reminder.delete()
        messages.success(request, 'Reminder deleted successfully!')
        return redirect('users:session_reminder_list')

    def get_success_url(self):
        return reverse_lazy('users:session_reminder_list')
