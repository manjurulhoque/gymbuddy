from django.urls import path
from .views import HomeView, DashboardView, PrivacyPolicyView, TermsConditionsView

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("privacy-policy/", PrivacyPolicyView.as_view(), name="privacy_policy"),
    path("terms-conditions/", TermsConditionsView.as_view(), name="terms_conditions"),
]
