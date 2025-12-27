from django.views.generic import TemplateView, UpdateView, ListView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from memberships.models import MembershipPlan
from users.mixins import StaffOrAboveRequiredMixin
from .models import Theme, Settings
from .forms import ThemeSelectionForm, ThemeForm


class HomeView(TemplateView):
    """Public home page view."""
    template_name = "home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['membership_plans'] = MembershipPlan.objects.filter(is_active=True).order_by('price')
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard view for authenticated users."""
    template_name = "dashboard/dashboard.html"
    login_url = "users:login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        return context


class PrivacyPolicyView(TemplateView):
    """Privacy Policy page view."""
    template_name = "privacy_policy.html"


class TermsConditionsView(TemplateView):
    """Terms & Conditions page view."""
    template_name = "terms_conditions.html"


class ThemeSettingsView(LoginRequiredMixin, UpdateView):
    """View for admins to change site-wide theme preference."""
    model = Settings
    form_class = ThemeSelectionForm
    template_name = "core/theme_settings.html"
    success_url = reverse_lazy("core:theme_settings")
    
    def get_object(self):
        """Get or create site settings (singleton)."""
        return Settings.get_settings()
    
    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, "Site theme updated successfully!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Add available themes to context."""
        context = super().get_context_data(**kwargs)
        context['available_themes'] = Theme.objects.filter(is_active=True).order_by('-is_default', 'name')
        context['current_theme'] = self.object.get_active_theme() if self.object else None
        return context


class ThemeListView(LoginRequiredMixin, ListView):
    """View to list all available themes (for preview)."""
    model = Theme
    template_name = "core/theme_list.html"
    context_object_name = "themes"
    
    def get_queryset(self):
        """Get active themes."""
        return Theme.objects.filter(is_active=True).order_by('-is_default', 'name')
    
    def get_context_data(self, **kwargs):
        """Add current site theme to context."""
        context = super().get_context_data(**kwargs)
        site_settings = Settings.get_settings()
        context['current_theme'] = site_settings.theme
        return context


class ThemeManageListView(StaffOrAboveRequiredMixin, ListView):
    """View to list all themes for management (create/update/delete)."""
    model = Theme
    template_name = "core/theme_manage_list.html"
    context_object_name = "themes"
    paginate_by = 20
    
    def get_queryset(self):
        """Get all themes, ordered by default first, then name."""
        return Theme.objects.all().order_by('-is_default', '-is_active', 'name')


class ThemeCreateView(StaffOrAboveRequiredMixin, CreateView):
    """View for creating a new theme."""
    model = Theme
    form_class = ThemeForm
    template_name = "core/theme_form.html"
    success_url = reverse_lazy("core:theme_manage_list")
    
    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, f"Theme '{form.instance.name}' created successfully!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Create New Theme"
        context['submit_button_text'] = "Create Theme"
        return context


class ThemeUpdateView(StaffOrAboveRequiredMixin, UpdateView):
    """View for updating an existing theme."""
    model = Theme
    form_class = ThemeForm
    template_name = "core/theme_form.html"
    success_url = reverse_lazy("core:theme_manage_list")
    
    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, f"Theme '{form.instance.name}' updated successfully!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Edit Theme: {self.object.name}"
        context['submit_button_text'] = "Update Theme"
        return context


class ThemeDeleteView(StaffOrAboveRequiredMixin, DeleteView):
    """View for deleting a theme."""
    model = Theme
    template_name = "core/theme_confirm_delete.html"
    success_url = reverse_lazy("core:theme_manage_list")
    
    def delete(self, request, *args, **kwargs):
        """Handle theme deletion."""
        theme = self.get_object()
        theme_name = theme.name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Theme '{theme_name}' deleted successfully!")
        return response
    
    def get_context_data(self, **kwargs):
        """Add theme info to context."""
        context = super().get_context_data(**kwargs)
        context['theme'] = self.object
        return context
