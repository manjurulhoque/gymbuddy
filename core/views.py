from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class HomeView(TemplateView):
    """Public home page view."""
    template_name = "home.html"


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
