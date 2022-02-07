from datetime import datetime
from django.db import models

from django.contrib.auth.models import User

STATUS_CHOICES = (
    ("PENDING", "PENDING"),
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("COMPLETED", "COMPLETED"),
    ("CANCELLED", "CANCELLED"),
)


class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    priority = models.IntegerField()
    completed = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.title


class TaskStatusChange(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    original_status = models.CharField(max_length=100, choices=STATUS_CHOICES)
    updated_status = models.CharField(max_length=100, choices=STATUS_CHOICES)
    changed_date = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.task.title} : {self.original_status} -> {self.updated_status}"


class UserPreferences(models.Model):
    reminder_enabled = models.BooleanField(default=False)
    reminder_time = models.TimeField(default="00:00:00")
    last_sent = models.DateTimeField(null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} => [{self.reminder_enabled} : {self.reminder_time}]"
