from django.urls import path
from .views import (
    HomeView, DashboardView, PrivacyPolicyView, TermsConditionsView,
    ThemeSettingsView, ThemeListView,
    ThemeManageListView, ThemeCreateView, ThemeUpdateView, ThemeDeleteView
)

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("privacy-policy/", PrivacyPolicyView.as_view(), name="privacy_policy"),
    path("terms-conditions/", TermsConditionsView.as_view(), name="terms_conditions"),
    path("settings/theme/", ThemeSettingsView.as_view(), name="theme_settings"),
    path("themes/", ThemeListView.as_view(), name="theme_list"),
    # Theme management URLs (staff/admin only)
    path("themes/manage/", ThemeManageListView.as_view(), name="theme_manage_list"),
    path("themes/create/", ThemeCreateView.as_view(), name="theme_create"),
    path("themes/<int:pk>/update/", ThemeUpdateView.as_view(), name="theme_update"),
    path("themes/<int:pk>/delete/", ThemeDeleteView.as_view(), name="theme_delete"),
]
