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
