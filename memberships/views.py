from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count
from django.utils import timezone
from users.mixins import StaffOrAboveRequiredMixin
from .models import MembershipPlan, Subscription, Payment
from .forms import SubscriptionForm, PaymentForm, QuickSubscriptionForm, UserSubscribeForm


class MembershipPlanListView(ListView):
    """List all active membership plans"""
    model = MembershipPlan
    template_name = 'memberships/plan_list.html'
    context_object_name = 'plans'
    
    def get_queryset(self):
        return MembershipPlan.objects.filter(is_active=True).order_by('price')


class SubscriptionListView(StaffOrAboveRequiredMixin, ListView):
    """List all subscriptions (staff only)"""
    model = Subscription
    template_name = 'memberships/subscription_list.html'
    context_object_name = 'subscriptions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Subscription.objects.select_related('user', 'plan').order_by('-created_at')
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by plan if provided
        plan_id = self.request.GET.get('plan')
        if plan_id:
            queryset = queryset.filter(plan_id=plan_id)
        
        # Search by username or email
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = MembershipPlan.objects.filter(is_active=True)
        context['status_choices'] = Subscription.Status.choices
        return context


class UserSubscriptionListView(LoginRequiredMixin, ListView):
    """List subscriptions for the current user"""
    model = Subscription
    template_name = 'memberships/my_subscriptions.html'
    context_object_name = 'subscriptions'
    
    def get_queryset(self):
        return Subscription.objects.filter(
            user=self.request.user
        ).select_related('plan').order_by('-created_at')


class SubscriptionDetailView(LoginRequiredMixin, DetailView):
    """View subscription details"""
    model = Subscription
    template_name = 'memberships/subscription_detail.html'
    context_object_name = 'subscription'
    
    def get_queryset(self):
        # Users can only view their own subscriptions unless they're staff
        if self.request.user.is_staff_or_above():
            return Subscription.objects.all()
        return Subscription.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payments'] = self.object.payments.all().order_by('-payment_date')
        context['total_paid'] = self.object.payments.filter(
            status=Payment.PaymentStatus.COMPLETED
        ).aggregate(total=Sum('amount'))['total'] or 0
        return context


class SubscriptionCreateView(StaffOrAboveRequiredMixin, CreateView):
    """Create a new subscription (staff only)"""
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'memberships/subscription_form.html'
    success_url = reverse_lazy('memberships:subscription_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Subscription created successfully!')
        return super().form_valid(form)


class SubscriptionUpdateView(StaffOrAboveRequiredMixin, UpdateView):
    """Update a subscription (staff only)"""
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'memberships/subscription_form.html'
    success_url = reverse_lazy('memberships:subscription_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Subscription updated successfully!')
        return super().form_valid(form)


class QuickSubscriptionCreateView(StaffOrAboveRequiredMixin, TemplateView):
    """Quick create subscription with auto-calculated dates"""
    template_name = 'memberships/quick_subscription.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = QuickSubscriptionForm()
        context['plans'] = MembershipPlan.objects.filter(is_active=True)
        return context
    
    def post(self, request, *args, **kwargs):
        form = QuickSubscriptionForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            plan = form.cleaned_data['plan']
            auto_renew = form.cleaned_data.get('auto_renew', False)
            
            # Check if user has an active subscription
            active_sub = Subscription.objects.filter(
                user=user,
                status=Subscription.Status.ACTIVE
            ).first()
            
            if active_sub:
                messages.warning(
                    request,
                    f'{user.username} already has an active subscription. '
                    'Please cancel or expire it first.'
                )
                return render(request, self.template_name, {'form': form})
            
            # Create subscription
            start_date = timezone.now()
            end_date = start_date + timezone.timedelta(days=plan.duration_days)
            
            subscription = Subscription.objects.create(
                user=user,
                plan=plan,
                status=Subscription.Status.ACTIVE,
                start_date=start_date,
                end_date=end_date,
                auto_renew=auto_renew
            )
            
            messages.success(
                request,
                f'Subscription created successfully for {user.username}!'
            )
            return redirect('memberships:subscription_detail', pk=subscription.pk)
        
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


class UserSubscribeView(LoginRequiredMixin, TemplateView):
    """View for users to subscribe to a plan"""
    template_name = 'memberships/user_subscribe.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan_id = self.kwargs.get('plan_id')
        plan = get_object_or_404(MembershipPlan, pk=plan_id, is_active=True)
        context['plan'] = plan
        context['form'] = UserSubscribeForm(plan_id=plan_id)
        
        # Check if user already has an active subscription
        active_sub = Subscription.objects.filter(
            user=self.request.user,
            status=Subscription.Status.ACTIVE
        ).first()
        context['has_active_subscription'] = active_sub is not None
        context['active_subscription'] = active_sub
        
        return context
    
    def post(self, request, *args, **kwargs):
        plan_id = self.kwargs.get('plan_id')
        plan = get_object_or_404(MembershipPlan, pk=plan_id, is_active=True)
        form = UserSubscribeForm(request.POST, plan_id=plan_id)
        
        if form.is_valid():
            auto_renew = form.cleaned_data.get('auto_renew', False)
            
            # Check if user already has an active subscription
            active_sub = Subscription.objects.filter(
                user=request.user,
                status=Subscription.Status.ACTIVE
            ).first()
            
            if active_sub:
                messages.warning(
                    request,
                    'You already have an active subscription. Please cancel or wait for it to expire before subscribing to a new plan.'
                )
                return redirect('memberships:my_subscriptions')
            
            # Create subscription with PENDING status
            # Staff will activate it after payment is processed
            start_date = timezone.now()
            end_date = start_date + timezone.timedelta(days=plan.duration_days)
            
            subscription = Subscription.objects.create(
                user=request.user,
                plan=plan,
                status=Subscription.Status.PENDING,
                start_date=start_date,
                end_date=end_date,
                auto_renew=auto_renew
            )
            
            messages.success(
                request,
                f'Subscription request created successfully! Your subscription will be activated once payment is processed. '
                f'Please contact the gym to complete your payment of ${plan.price}.'
            )
            return redirect('memberships:subscription_detail', pk=subscription.pk)
        
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


class PaymentListView(StaffOrAboveRequiredMixin, ListView):
    """List all payments (staff only)"""
    model = Payment
    template_name = 'memberships/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Payment.objects.select_related(
            'subscription__user', 'subscription__plan'
        ).order_by('-payment_date')
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by payment method if provided
        method = self.request.GET.get('method')
        if method:
            queryset = queryset.filter(payment_method=method)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(subscription__user__username__icontains=search) |
                Q(subscription__user__email__icontains=search) |
                Q(transaction_id__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_revenue'] = Payment.objects.filter(
            status=Payment.PaymentStatus.COMPLETED
        ).aggregate(total=Sum('amount'))['total'] or 0
        context['status_choices'] = Payment.PaymentStatus.choices
        context['method_choices'] = Payment.PaymentMethod.choices
        return context


class PaymentCreateView(StaffOrAboveRequiredMixin, CreateView):
    """Create a new payment (staff only)"""
    model = Payment
    form_class = PaymentForm
    template_name = 'memberships/payment_form.html'
    
    def get_success_url(self):
        return reverse_lazy('memberships:subscription_detail', kwargs={'pk': self.object.subscription.pk})
    
    def get_initial(self):
        initial = super().get_initial()
        subscription_id = self.request.GET.get('subscription')
        if subscription_id:
            try:
                subscription = Subscription.objects.get(pk=subscription_id)
                initial['subscription'] = subscription
                initial['amount'] = subscription.plan.price
            except Subscription.DoesNotExist:
                pass
        return initial
    
    def form_valid(self, form):
        # If payment is completed, update subscription status to active
        if form.cleaned_data['status'] == Payment.PaymentStatus.COMPLETED:
            subscription = form.cleaned_data['subscription']
            if subscription.status == Subscription.Status.PENDING:
                subscription.status = Subscription.Status.ACTIVE
                subscription.save()
        
        messages.success(self.request, 'Payment recorded successfully!')
        return super().form_valid(form)


class PaymentUpdateView(StaffOrAboveRequiredMixin, UpdateView):
    """Update a payment (staff only)"""
    model = Payment
    form_class = PaymentForm
    template_name = 'memberships/payment_form.html'
    
    def get_success_url(self):
        return reverse_lazy('memberships:subscription_detail', kwargs={'pk': self.object.subscription.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment updated successfully!')
        return super().form_valid(form)


class MembershipDashboardView(StaffOrAboveRequiredMixin, TemplateView):
    """Dashboard with membership statistics"""
    template_name = 'memberships/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Subscription statistics
        context['total_subscriptions'] = Subscription.objects.count()
        context['active_subscriptions'] = Subscription.objects.filter(
            status=Subscription.Status.ACTIVE
        ).count()
        context['expired_subscriptions'] = Subscription.objects.filter(
            status=Subscription.Status.EXPIRED
        ).count()
        context['pending_subscriptions'] = Subscription.objects.filter(
            status=Subscription.Status.PENDING
        ).count()
        
        # Payment statistics
        context['total_revenue'] = Payment.objects.filter(
            status=Payment.PaymentStatus.COMPLETED
        ).aggregate(total=Sum('amount'))['total'] or 0
        context['pending_payments'] = Payment.objects.filter(
            status=Payment.PaymentStatus.PENDING
        ).count()
        
        # Recent subscriptions
        context['recent_subscriptions'] = Subscription.objects.select_related(
            'user', 'plan'
        ).order_by('-created_at')[:10]
        
        # Recent payments
        context['recent_payments'] = Payment.objects.select_related(
            'subscription__user', 'subscription__plan'
        ).order_by('-payment_date')[:10]
        
        # Expiring soon (within 7 days)
        seven_days_from_now = timezone.now() + timezone.timedelta(days=7)
        context['expiring_soon'] = Subscription.objects.filter(
            status=Subscription.Status.ACTIVE,
            end_date__lte=seven_days_from_now,
            end_date__gte=timezone.now()
        ).select_related('user', 'plan').order_by('end_date')
        
        # Plan distribution
        context['plan_distribution'] = Subscription.objects.filter(
            status=Subscription.Status.ACTIVE
        ).values('plan__display_name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return context
