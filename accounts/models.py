from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class User(AbstractUser):
    email = models.EmailField(unique=True)
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('user', 'User'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_verified = models.BooleanField(default=False)
    failed_attempts = models.IntegerField(default=0)
    blocked_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email
    

class OTP(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)  

    class Meta:
        indexes = [
            models.Index(fields=['user', 'otp']),
            models.Index(fields=['created_at']), 
        ]


    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"{self.user.email} - {self.otp}"
    
from django.conf import settings

class Task(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_tasks'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tasks'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
   

    class Meta:
        ordering = ['-created_at']  #  latest first
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['created_by']),
            models.Index(fields=['assigned_to', 'status']), 
        ]

    def __str__(self):
        return self.title
    

class AuditLog(models.Model):
    ACTION_TYPES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    user_email = models.EmailField(null=True, blank=True)  # NEW
 
    action = models.TextField()

    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPES,
        default='CREATE'
    )

    object_id = models.IntegerField(null=True, blank=True)
    model_name = models.CharField(max_length=100, null=True, blank=True)
    old_data = models.JSONField(null=True, blank=True)
    new_data = models.JSONField(null=True, blank=True)

    field_name = models.CharField(max_length=100, null=True, blank=True)
    old_value = models.CharField(max_length=255, null=True, blank=True)
    new_value = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user_email} - {self.action_type}" 