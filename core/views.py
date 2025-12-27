from django.views.generic import TemplateView, UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from memberships.models import MembershipPlan
from .models import Theme, Settings
from .forms import ThemeSelectionForm


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
