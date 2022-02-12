from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.test import Client, RequestFactory, TestCase
from django.utils.timezone import make_aware

from .models import Task, TaskStatusChange, UserPreferences
from .tasks import get_email_content, send_reports


class ViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create(username="test", email="test@test.org", password="test")
        self.client.force_login(self.user)

        self.anon_client = Client()

    def test_index_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/tasks/")

    def test_unauthenticated(self):
        response = self.anon_client.get("/tasks/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/user/login/?next=/tasks/")

    def test_authenticated(self):
        response = self.client.get("/tasks/")
        self.assertEqual(response.status_code, 200)

    def test_authenticated_create_task(self):
        response = self.client.post("/add_task/",
                                    urlencode({"title": "Task 1", "description": "This is task 1", "priority": 1}),
                                    content_type="application/x-www-form-urlencoded")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/tasks/")
        self.assertEqual(Task.objects.get(id=1).title, "Task 1")
        self.assertEqual(Task.objects.get(id=1).description, "This is task 1")
        self.assertEqual(Task.objects.get(id=1).priority, 1)

    def test_with_tasks(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1)
        Task.objects.create(user=self.user, title="Task 2", priority=2)
        response = self.client.get("/tasks/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["completed_tasks"], 0)
        self.assertEqual(response.context["total_tasks"], 2)

    def test_with_completed_tasks(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1, completed=True)
        Task.objects.create(user=self.user, title="Task 2", priority=2)
        response = self.client.get("/tasks/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["completed_tasks"], 1)
        self.assertEqual(response.context["total_tasks"], 2)

    def test_with_completed_tasks_and_filter(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1, completed=True)
        Task.objects.create(user=self.user, title="Task 2", priority=2)
        response = self.client.get("/tasks/?filter=completed")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["completed_tasks"], 1)
        self.assertEqual(response.context["total_tasks"], 2)

    def test_with_completed_tasks_and_incompleted_filter(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1, completed=True)
        Task.objects.create(user=self.user, title="Task 2", priority=2)
        response = self.client.get("/tasks/?filter=pending")
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Task 2")
        self.assertNotContains(response, "Task 1")

        self.assertEqual(response.context["completed_tasks"], 1)
        self.assertEqual(response.context["total_tasks"], 2)

    def test_update_with_priorities_logic(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1)
        Task.objects.create(user=self.user, title="Task 2", priority=2)
        Task.objects.create(user=self.user, title="Task 3", priority=3)

        response = self.client.post("/update_task/1",
                                    urlencode({"title": "Task 1", "description": "task 1 description", "priority": "1"}),
                                    content_type="application/x-www-form-urlencoded")
        response = self.client.post("/update_task/2",
                                    urlencode({"title": "Task 2", "description": "task 2 description", "priority": "3"}),
                                    content_type="application/x-www-form-urlencoded")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/tasks/")

        self.assertEqual(Task.objects.get(id=1).priority, 1)
        self.assertEqual(Task.objects.get(id=2).priority, 3)
        self.assertEqual(Task.objects.get(id=3).priority, 4)

        self.assertEqual(Task.objects.get(id=1).description, "task 1 description")
        self.assertEqual(Task.objects.get(id=2).description, "task 2 description")

    def test_delete_task(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1)
        response = self.client.post("/delete_task/1")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/tasks/")
        self.assertEqual(Task.objects.filter(id=1).count(), 0)

        response = self.client.post("/delete_task/999")
        self.assertEqual(response.status_code, 404)

    def test_toggle_complete_task(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1)
        response = self.client.get("/toggle_complete_task/1")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/tasks/")
        self.assertEqual(Task.objects.get(id=1).completed, True)

        response = self.anon_client.get("/toggle_complete_task/1")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/user/login/")

    def test_preferences(self):
        response = self.client.get("/user/preferences/")
        self.assertEqual(response.status_code, 200)

    def test_preferences_update(self):
        response = self.client.post("/user/preferences/",
                                    urlencode({"reminder_enabled": "on", "reminder_time": "10:00:00"}),
                                    content_type="application/x-www-form-urlencoded")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/tasks/")

        self.assertEqual(UserPreferences.objects.get(user=self.user).reminder_enabled, True)
        self.assertEqual(str(UserPreferences.objects.get(user=self.user).reminder_time), "10:00:00")


class APITests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="test", password="test")
        self.client.force_login(self.user)

    def test_create_task(self):
        response = self.client.post("/api/tasks/",
                                    {"title": "Task 1", "description": "This is task 1", "priority": 1},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Task.objects.get(id=1).title, "Task 1")
        self.assertEqual(Task.objects.get(id=1).description, "This is task 1")
        self.assertEqual(Task.objects.get(id=1).priority, 1)

    def test_create_task_with_invalid_details(self):
        response = self.client.post("/api/tasks/",
                                    {"title": "", "description": "", "priority": "bbb"},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_list_tasks(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1)
        Task.objects.create(user=self.user, title="Task 2", priority=2)

        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, 200)

        result = response.json()

        self.assertEqual(result[0]["title"], "Task 1")
        self.assertEqual(result[0]["description"], "")
        self.assertEqual(result[0]["priority"], 1)
        self.assertEqual(result[0]["completed"], False)

        self.assertEqual(result[1]["title"], "Task 2")
        self.assertEqual(result[1]["description"], "")
        self.assertEqual(result[1]["priority"], 2)
        self.assertEqual(result[1]["completed"], False)

    def test_list_tasks_with_filter(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1)
        Task.objects.create(user=self.user, title="Task 2", priority=2, completed=True)
        Task.objects.create(user=self.user, title="Task 3", priority=3)

        response = self.client.get("/api/tasks/?completed=True")
        self.assertEqual(response.status_code, 200)

        result = response.json()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Task 2")

    def test_delete_task(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1)
        response = self.client.delete("/api/tasks/1/")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Task.objects.filter(id=1).count(), 0)

        response = self.client.delete("/api/tasks/999/")
        self.assertEqual(response.status_code, 404)

    def test_update_task(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1)
        response = self.client.patch("/api/tasks/1/",
                                     {"title": "Task 2", "description": "This is task 2", "priority": 2},
                                     content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.get(id=1).title, "Task 2")
        self.assertEqual(Task.objects.get(id=1).description, "This is task 2")
        self.assertEqual(Task.objects.get(id=1).priority, 2)

    def test_task_change(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1, status="PENDING")

        response = self.client.patch("/api/tasks/1/", {"status": "IN_PROGRESS"}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.get(id=1).status, "IN_PROGRESS")

        self.assertEqual(TaskStatusChange.objects.filter(task=Task.objects.get(id=1)).count(), 1)
        self.assertEqual(TaskStatusChange.objects.get(task=Task.objects.get(id=1)).original_status, "PENDING")
        self.assertEqual(TaskStatusChange.objects.get(task=Task.objects.get(id=1)).updated_status, "IN_PROGRESS")

        response = self.client.patch("/api/tasks/1/", {"status": "COMPLETED"}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.get(id=1).status, "COMPLETED")

        self.assertEqual(TaskStatusChange.objects.filter(task=Task.objects.get(id=1)).count(), 2)
        self.assertEqual(TaskStatusChange.objects.get(task=Task.objects.get(id=1), id=2).original_status, "IN_PROGRESS")
        self.assertEqual(TaskStatusChange.objects.get(task=Task.objects.get(id=1), id=2).updated_status, "COMPLETED")

    def test_history_api(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1, status="PENDING")

        self.client.patch("/api/tasks/1/", {"status": "IN_PROGRESS"}, content_type="application/json")
        self.client.patch("/api/tasks/1/", {"status": "COMPLETED"}, content_type="application/json")

        response = self.client.get("/api/tasks/1/history/")
        self.assertEqual(response.status_code, 200)

        result = response.json()
        self.assertEqual(len(result), 2)

        self.assertEqual(result[0]["original_status"], "PENDING")
        self.assertEqual(result[0]["updated_status"], "IN_PROGRESS")

        self.assertEqual(result[1]["original_status"], "IN_PROGRESS")
        self.assertEqual(result[1]["updated_status"], "COMPLETED")

    def test_get_deleted_task(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1)
        self.client.delete("/api/tasks/1/")

        response = self.client.get("/api/tasks/1/")
        self.assertEqual(response.status_code, 404)


class CeleryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="test", password="test")

    def test_daily_reminder(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1)

        UserPreferences.objects.create(user=self.user, reminder_enabled=True, reminder_time=make_aware(datetime.now() - timedelta(seconds=10)).time())

        send_reports.apply()

        self.assertLessEqual(UserPreferences.objects.get(user=self.user).last_sent, make_aware(datetime.now()))

    def test_missed_reminder(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1)

        UserPreferences.objects.create(user=self.user, reminder_enabled=True,
                                       reminder_time=make_aware(datetime.now() - timedelta(seconds=10)).time(),
                                       last_sent=make_aware(datetime.now() - timedelta(days=1)))
        send_reports.apply()

        self.assertLessEqual(UserPreferences.objects.get(user=self.user).last_sent, make_aware(datetime.now()))

    def test_report_content(self):
        Task.objects.create(user=self.user, title="Task 1", priority=1)
        Task.objects.create(user=self.user, title="Task 2", priority=2, status="IN_PROGRESS")
        Task.objects.create(user=self.user, title="Task 3", priority=3, status="COMPLETED", completed=True)
        Task.objects.create(user=self.user, title="Task 4", priority=4, status="CANCELLED")

        email = get_email_content(self.user)

        self.assertEqual(
            email, "Hello test!\n\nHere is your tasks summary:\n\n1 pending task(s).\n\n1 in_progress task(s).\n\n1 completed task(s).\n\n1 cancelled task(s).\n\n\nThank you!")


class MiscellaneousTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="test", password="test")

    def test_repr_models(self):
        task = Task(user=self.user, title="Task 1", priority=1)
        self.assertEqual(repr(task), "<Task: Task 1>")

        task_change = TaskStatusChange(task=task, original_status="PENDING", updated_status="IN_PROGRESS")
        self.assertEqual(repr(task_change), "<TaskStatusChange: Task 1 : PENDING -> IN_PROGRESS>")

        pref = UserPreferences(user=self.user, reminder_enabled=True, reminder_time="10:00:00")
        self.assertEqual(repr(pref), "<UserPreferences: test => [True : 10:00:00]>")
