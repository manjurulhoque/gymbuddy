from django.contrib.auth.models import AbstractUser
from django.db import models


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
