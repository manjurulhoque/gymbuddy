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
