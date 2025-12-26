from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from users.models import User


class MembershipPlan(models.Model):
    """
    Membership plans available for subscription (Basic, Premium, VIP)
    """
    
    class PlanType(models.TextChoices):
        BASIC = "BASIC", "Basic"
        PREMIUM = "PREMIUM", "Premium"
        VIP = "VIP", "VIP"
    
    name = models.CharField(
        max_length=50,
        choices=PlanType.choices,
        unique=True,
        help_text="Plan name"
    )
    display_name = models.CharField(
        max_length=100,
        help_text="Display name for the plan"
    )
    description = models.TextField(
        blank=True,
        help_text="Plan description and features"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Monthly price"
    )
    duration_days = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1)],
        help_text="Subscription duration in days"
    )
    features = models.JSONField(
        default=list,
        blank=True,
        help_text="List of features included in this plan"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this plan is currently available"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Membership Plan"
        verbose_name_plural = "Membership Plans"
        ordering = ['price']
    
    def __str__(self):
        return f"{self.get_name_display()} - ${self.price}/month"
    
    def get_duration_months(self):
        """Get duration in months (approximate)"""
        return round(self.duration_days / 30, 1)


class Subscription(models.Model):
    """
    User subscription to a membership plan
    """
    
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        EXPIRED = "EXPIRED", "Expired"
        CANCELLED = "CANCELLED", "Cancelled"
        PENDING = "PENDING", "Pending"
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        help_text="Subscribed user"
    )
    plan = models.ForeignKey(
        MembershipPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        help_text="Membership plan"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Subscription status"
    )
    start_date = models.DateTimeField(
        default=timezone.now,
        help_text="Subscription start date"
    )
    end_date = models.DateTimeField(
        help_text="Subscription end date"
    )
    auto_renew = models.BooleanField(
        default=False,
        help_text="Whether subscription should auto-renew"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.get_name_display()} ({self.get_status_display()})"
    
    def is_active(self):
        """Check if subscription is currently active"""
        now = timezone.now()
        return (
            self.status == self.Status.ACTIVE and
            self.start_date <= now <= self.end_date
        )
    
    def is_expired(self):
        """Check if subscription has expired"""
        return timezone.now() > self.end_date
    
    def days_remaining(self):
        """Get number of days remaining in subscription"""
        if self.is_expired():
            return 0
        delta = self.end_date - timezone.now()
        return max(0, delta.days)
    
    def save(self, *args, **kwargs):
        """Auto-calculate end_date if not set"""
        if not self.end_date:
            self.end_date = self.start_date + timezone.timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)


class Payment(models.Model):
    """
    Payment history for subscriptions
    """
    
    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Cash"
        CARD = "CARD", "Card"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"
        CHEQUE = "CHEQUE", "Cheque"
        OTHER = "OTHER", "Other"
    
    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="Associated subscription"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Payment amount"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        help_text="Payment method used"
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        help_text="Payment status"
    )
    payment_date = models.DateTimeField(
        default=timezone.now,
        help_text="Date of payment"
    )
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Transaction ID or reference number"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the payment"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['subscription', 'status']),
            models.Index(fields=['payment_date']),
        ]
    
    def __str__(self):
        return f"${self.amount} - {self.subscription.user.username} ({self.get_status_display()})"
