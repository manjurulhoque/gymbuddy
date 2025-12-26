from django.urls import path
from . import views

app_name = 'memberships'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.MembershipDashboardView.as_view(), name='dashboard'),
    
    # Plans
    path('plans/', views.MembershipPlanListView.as_view(), name='plan_list'),
    
    # Subscriptions
    path('subscriptions/', views.SubscriptionListView.as_view(), name='subscription_list'),
    path('subscriptions/my/', views.UserSubscriptionListView.as_view(), name='my_subscriptions'),
    path('subscriptions/create/', views.SubscriptionCreateView.as_view(), name='subscription_create'),
    path('subscriptions/quick/', views.QuickSubscriptionCreateView.as_view(), name='quick_subscription_create'),
    path('subscriptions/<int:pk>/', views.SubscriptionDetailView.as_view(), name='subscription_detail'),
    path('subscriptions/<int:pk>/update/', views.SubscriptionUpdateView.as_view(), name='subscription_update'),
    
    # Payments
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/create/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('payments/<int:pk>/update/', views.PaymentUpdateView.as_view(), name='payment_update'),
]

