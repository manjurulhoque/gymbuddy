from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import TemplateView, View, ListView, CreateView, UpdateView, DeleteView, FormView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.db import models
from django.urls import reverse_lazy
from .models import User
from .forms import UserForm, UserUpdateForm, ProfileForm, ProfilePasswordChangeForm
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
