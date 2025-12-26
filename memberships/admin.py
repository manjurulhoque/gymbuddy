from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import MembershipPlan, Subscription, Payment


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    """Admin interface for MembershipPlan"""
    
    list_display = ['name', 'display_name', 'price', 'duration_days', 'is_active', 'created_at']
    list_filter = ['name', 'is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Plan Information', {
            'fields': ('name', 'display_name', 'description', 'is_active')
        }),
        ('Pricing', {
            'fields': ('price', 'duration_days')
        }),
        ('Features', {
            'fields': ('features',),
            'description': 'Enter features as a JSON array, e.g., ["Feature 1", "Feature 2"]'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for Subscription"""
    
    list_display = ['user', 'plan', 'status', 'start_date', 'end_date', 'days_remaining_display', 'auto_renew', 'created_at']
    list_filter = ['status', 'plan', 'auto_renew', 'start_date', 'end_date']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'status_display']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Subscription Information', {
            'fields': ('user', 'plan', 'status', 'status_display')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Settings', {
            'fields': ('auto_renew',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def days_remaining_display(self, obj):
        """Display days remaining with color coding"""
        days = obj.days_remaining()
        if days == 0:
            color = 'red'
            text = 'Expired'
        elif days <= 7:
            color = 'orange'
            text = f'{days} days'
        else:
            color = 'green'
            text = f'{days} days'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, text
        )
    days_remaining_display.short_description = 'Days Remaining'
    
    def status_display(self, obj):
        """Display status with color coding"""
        colors = {
            'ACTIVE': 'green',
            'EXPIRED': 'red',
            'CANCELLED': 'gray',
            'PENDING': 'orange',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment"""
    
    list_display = ['subscription', 'amount', 'payment_method', 'status', 'payment_date', 'transaction_id', 'created_at']
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = [
        'subscription__user__username',
        'subscription__user__email',
        'transaction_id',
        'notes'
    ]
    readonly_fields = ['created_at', 'updated_at', 'status_display']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('subscription', 'amount', 'payment_method', 'status', 'status_display')
        }),
        ('Transaction Details', {
            'fields': ('payment_date', 'transaction_id', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        """Display status with color coding"""
        colors = {
            'COMPLETED': 'green',
            'PENDING': 'orange',
            'FAILED': 'red',
            'REFUNDED': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
