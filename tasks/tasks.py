from django.core.mail import send_mail
from datetime import datetime, timedelta

from celery.decorators import periodic_task

from task_manager.celery import app
from tasks.models import STATUS_CHOICES, Task, UserPreferences


def process_email(user):
    email_content = f"Hello {user.username}!\n\n"
    email_content += "Here is your tasks summary:\n"
    all_tasks = Task.objects.filter(user=user, deleted=False)
    for status in STATUS_CHOICES:
        tasks = all_tasks.filter(status=status[0])
        if tasks.exists():
            email_content += f"\n{len(tasks)} {status[1].lower()} task(s).\n"
    email_content += "\n\n"
    email_content += "Thank you!"
    send_mail("Tasks summary", email_content, "tasks@task_manager.org", [user.email], fail_silently=False,)


@periodic_task(run_every=timedelta(seconds=30))
def send_reports():
    current_time = datetime.now()
    matching_users = UserPreferences.objects.filter(reminder_enabled=True, reminder_time__range=(current_time - timedelta(seconds=30), current_time))
    if len(matching_users) == 0:
        print("No matching users found")
    for user_prefs in matching_users:
        print("Processing", user_prefs.user)
        process_email(user_prefs.user)
