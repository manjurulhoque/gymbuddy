from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, TrainerTraineeAssignment, Attendance


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin interface for User model"""
    
    list_display = ['username', 'email', 'role', 'first_name', 'last_name', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('role', 'phone_number', 'profile_picture')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': ('role', 'phone_number', 'email', 'first_name', 'last_name')
        }),
    )


@admin.register(TrainerTraineeAssignment)
class TrainerTraineeAssignmentAdmin(admin.ModelAdmin):
    """Admin interface for TrainerTraineeAssignment model"""
    
    list_display = ['trainer', 'trainee', 'assigned_by', 'assigned_at', 'is_active']
    list_filter = ['is_active', 'assigned_at']
    search_fields = ['trainer__username', 'trainer__first_name', 'trainer__last_name', 
                     'trainee__username', 'trainee__first_name', 'trainee__last_name']
    readonly_fields = ['assigned_at', 'created_at', 'updated_at']
    ordering = ['-assigned_at']
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('trainer', 'trainee', 'assigned_by', 'is_active')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('assigned_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Admin interface for Attendance model"""
    
    list_display = ['trainee', 'check_in', 'check_out', 'marked_by', 'duration_display', 'is_checked_in_display']
    list_filter = ['check_in', 'marked_by', 'trainee']
    search_fields = ['trainee__username', 'trainee__first_name', 'trainee__last_name']
    readonly_fields = ['created_at', 'updated_at', 'duration_display', 'is_checked_in_display']
    ordering = ['-check_in']
    date_hierarchy = 'check_in'
    
    fieldsets = (
        ('Attendance Details', {
            'fields': ('trainee', 'check_in', 'check_out', 'marked_by')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Computed Fields', {
            'fields': ('duration_display', 'is_checked_in_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def duration_display(self, obj):
        """Display duration in a readable format"""
        if obj.duration:
            hours = obj.duration // 60
            minutes = obj.duration % 60
            if hours > 0:
                return f"{hours}h {minutes}m"
            return f"{minutes}m"
        return "—"
    duration_display.short_description = "Duration"
    
    def is_checked_in_display(self, obj):
        """Display check-in status"""
        return "Yes" if obj.is_checked_in else "No"
    is_checked_in_display.short_description = "Currently Checked In"
    is_checked_in_display.boolean = True
