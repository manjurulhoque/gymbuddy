from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.generic import TemplateView, View, ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.db import models
from django.http import JsonResponse
from django.urls import reverse_lazy
from .models import User
from .forms import UserForm, UserUpdateForm
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
        
        # Filter based on user role
        if current_user.is_manager():
            # Managers can only see Trainees
            queryset = queryset.filter(role=User.Role.TRAINEE)
        elif current_user.is_owner():
            # Owners can see Trainees and Managers
            queryset = queryset.filter(role__in=[User.Role.TRAINEE, User.Role.MANAGER])
        # Super Admin can see all users
        
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
        context['form'] = UserForm(user=self.request.user)
        return context


class UserCreateView(StaffOrAboveRequiredMixin, CreateView):
    """Create view for users (used via AJAX in modal)."""
    model = User
    form_class = UserForm
    login_url = "users:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, f'User {user.get_full_name() or user.username} created successfully!')
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'User {user.get_full_name() or user.username} created successfully!',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.get_full_name() or user.username,
                    'email': user.email,
                    'role': user.get_role_display(),
                }
            })
        
        return redirect('users:user_list')

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('users:user_list')


class UserUpdateView(StaffOrAboveRequiredMixin, UpdateView):
    """Update view for users."""
    model = User
    form_class = UserUpdateForm
    template_name = "users/user_form.html"
    login_url = "users:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, f'User {user.get_full_name() or user.username} updated successfully!')
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'User {user.get_full_name() or user.username} updated successfully!',
            })
        
        return redirect('users:user_list')

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        
        return super().form_invalid(form)

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
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'User {username} deleted successfully!',
            })
        
        return redirect('users:user_list')

    def get_success_url(self):
        return reverse_lazy('users:user_list')
