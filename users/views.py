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
from .models import User, TrainerTraineeAssignment, Attendance
from .forms import UserForm, UserUpdateForm, ProfileForm, ProfilePasswordChangeForm, TrainerTraineeAssignmentForm
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
