from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model with role-based access control.
    """

    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        OWNER = "OWNER", "Owner"
        MANAGER = "MANAGER", "Manager"
        TRAINER = "TRAINER", "Trainer"
        TRAINEE = "TRAINEE", "Trainee"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.TRAINEE,
        help_text="User's role in the system",
    )
    phone_number = models.CharField(
        max_length=20, blank=True, null=True, help_text="Contact phone number"
    )
    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True,
        help_text="User profile picture",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    def is_owner(self):
        return self.role == self.Role.OWNER

    def is_manager(self):
        return self.role == self.Role.MANAGER

    def is_trainer(self):
        return self.role == self.Role.TRAINER

    def is_trainee(self):
        return self.role == self.Role.TRAINEE

    def is_staff_or_above(self):
        """Check if user has staff-level access or above"""
        return self.role in [self.Role.SUPER_ADMIN, self.Role.OWNER, self.Role.MANAGER]


class TrainerTraineeAssignment(models.Model):
    """
    Model to track assignments between trainers and trainees.
    """
    trainer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_trainees',
        limit_choices_to={'role': User.Role.TRAINER},
        help_text="The trainer assigned to this trainee"
    )
    trainee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_trainer',
        limit_choices_to={'role': User.Role.TRAINEE},
        help_text="The trainee assigned to this trainer"
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments_made',
        help_text="User who made this assignment"
    )
    assigned_at = models.DateTimeField(auto_now_add=True, help_text="When the assignment was created")
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this assignment"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this assignment is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Trainer-Trainee Assignment"
        verbose_name_plural = "Trainer-Trainee Assignments"
        ordering = ['-assigned_at']
        unique_together = [['trainer', 'trainee']]
        indexes = [
            models.Index(fields=['trainer', 'is_active']),
            models.Index(fields=['trainee', 'is_active']),
        ]

    def __str__(self):
        return f"{self.trainer.get_full_name() or self.trainer.username} -> {self.trainee.get_full_name() or self.trainee.username}"


class Attendance(models.Model):
    """
    Model to track attendance (check-in/check-out) for trainees.
    """
    trainee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendances',
        limit_choices_to={'role': User.Role.TRAINEE},
        help_text="The trainee whose attendance is being tracked"
    )
    check_in = models.DateTimeField(
        help_text="Check-in time"
    )
    check_out = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Check-out time (null if still checked in)"
    )
    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendances',
        limit_choices_to={'role__in': [User.Role.TRAINER, User.Role.MANAGER, User.Role.OWNER, User.Role.SUPER_ADMIN]},
        help_text="Trainer or staff member who marked this attendance (null if self-check-in)"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this attendance"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Attendance"
        verbose_name_plural = "Attendances"
        ordering = ['-check_in']
        indexes = [
            models.Index(fields=['trainee', '-check_in']),
            models.Index(fields=['check_in']),
            models.Index(fields=['marked_by']),
        ]

    def __str__(self):
        check_out_status = f" - {self.check_out.strftime('%H:%M')}" if self.check_out else " (Checked In)"
        return f"{self.trainee.get_full_name() or self.trainee.username} - {self.check_in.strftime('%Y-%m-%d %H:%M')}{check_out_status}"

    @property
    def duration(self):
        """Calculate duration in minutes if checked out."""
        if self.check_out:
            delta = self.check_out - self.check_in
            return int(delta.total_seconds() / 60)
        return None

    def get_duration_display(self):
        """Get formatted duration string."""
        if not self.duration:
            return "—"
        hours = self.duration // 60
        minutes = self.duration % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    @property
    def is_checked_in(self):
        """Check if trainee is currently checked in."""
        return self.check_out is None

    @property
    def date(self):
        """Get the date of attendance."""
        return self.check_in.date()


class TrainerAvailability(models.Model):
    """
    Model to track trainer availability schedules.
    """
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    trainer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='availabilities',
        limit_choices_to={'role': User.Role.TRAINER},
        help_text="The trainer whose availability this is"
    )
    day_of_week = models.IntegerField(
        choices=DayOfWeek.choices,
        help_text="Day of the week (0=Monday, 6=Sunday)"
    )
    start_time = models.TimeField(
        help_text="Start time of availability"
    )
    end_time = models.TimeField(
        help_text="End time of availability"
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Whether this time slot is currently available"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Trainer Availability"
        verbose_name_plural = "Trainer Availabilities"
        ordering = ['trainer', 'day_of_week', 'start_time']
        unique_together = [['trainer', 'day_of_week', 'start_time', 'end_time']]
        indexes = [
            models.Index(fields=['trainer', 'day_of_week', 'is_available']),
        ]

    def __str__(self):
        return f"{self.trainer.get_full_name() or self.trainer.username} - {self.get_day_of_week_display()} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"


class TrainingSession(models.Model):
    """
    Model to track booked training sessions/appointments.
    """
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        CONFIRMED = "CONFIRMED", "Confirmed"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        NO_SHOW = "NO_SHOW", "No Show"

    trainer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='training_sessions',
        limit_choices_to={'role': User.Role.TRAINER},
        help_text="The trainer for this session"
    )
    trainee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='booked_sessions',
        limit_choices_to={'role': User.Role.TRAINEE},
        help_text="The trainee for this session"
    )
    session_date = models.DateField(
        help_text="Date of the training session"
    )
    start_time = models.TimeField(
        help_text="Start time of the session"
    )
    end_time = models.TimeField(
        help_text="End time of the session"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        help_text="Current status of the session"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this session"
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the session was cancelled (if applicable)"
    )
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_sessions',
        help_text="User who cancelled the session"
    )
    cancellation_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for cancellation"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_sessions',
        help_text="User who created this booking"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Training Session"
        verbose_name_plural = "Training Sessions"
        ordering = ['session_date', 'start_time']
        indexes = [
            models.Index(fields=['trainer', 'session_date', 'status']),
            models.Index(fields=['trainee', 'session_date', 'status']),
            models.Index(fields=['session_date', 'start_time']),
        ]

    def __str__(self):
        return f"{self.trainee.get_full_name() or self.trainee.username} with {self.trainer.get_full_name() or self.trainer.username} - {self.session_date} {self.start_time.strftime('%H:%M')}"

    @property
    def session_datetime_start(self):
        """Get the full datetime for session start."""
        from django.utils import timezone
        return timezone.make_aware(
            timezone.datetime.combine(self.session_date, self.start_time)
        )

    @property
    def session_datetime_end(self):
        """Get the full datetime for session end."""
        from django.utils import timezone
        return timezone.make_aware(
            timezone.datetime.combine(self.session_date, self.end_time)
        )

    @property
    def is_upcoming(self):
        """Check if session is in the future."""
        from django.utils import timezone
        return self.session_datetime_start > timezone.now()

    @property
    def is_past(self):
        """Check if session is in the past."""
        from django.utils import timezone
        return self.session_datetime_end < timezone.now()

    @property
    def duration_minutes(self):
        """Calculate session duration in minutes."""
        from datetime import datetime
        start = datetime.combine(self.session_date, self.start_time)
        end = datetime.combine(self.session_date, self.end_time)
        delta = end - start
        return int(delta.total_seconds() / 60)


class SessionReminder(models.Model):
    """
    Model to track reminders for training sessions.
    """
    class ReminderType(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        SMS = "SMS", "SMS"
        PUSH = "PUSH", "Push Notification"

    session = models.ForeignKey(
        TrainingSession,
        on_delete=models.CASCADE,
        related_name='reminders',
        help_text="The training session this reminder is for"
    )
    reminder_type = models.CharField(
        max_length=20,
        choices=ReminderType.choices,
        default=ReminderType.EMAIL,
        help_text="Type of reminder"
    )
    reminder_time = models.DateTimeField(
        help_text="When to send the reminder"
    )
    sent = models.BooleanField(
        default=False,
        help_text="Whether the reminder has been sent"
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the reminder was sent"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Session Reminder"
        verbose_name_plural = "Session Reminders"
        ordering = ['reminder_time']
        indexes = [
            models.Index(fields=['session', 'sent']),
            models.Index(fields=['reminder_time', 'sent']),
        ]

    def __str__(self):
        return f"Reminder for {self.session} - {self.reminder_time.strftime('%Y-%m-%d %H:%M')}"

    @property
    def is_due(self):
        """Check if reminder is due to be sent."""
        from django.utils import timezone
        return not self.sent and self.reminder_time <= timezone.now()
