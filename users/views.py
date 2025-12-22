from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods


class LoginView(TemplateView):
    """
    Custom login view with role-based authentication using class-based view.
    """
    template_name = 'users/login.html'

    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users to home page."""
        if request.user.is_authenticated:
            return redirect('home')
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
                    next_url = request.GET.get('next', 'home')
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
        return redirect('home')
