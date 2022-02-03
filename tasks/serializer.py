from rest_framework.serializers import ModelSerializer
from tasks.models import Task, TaskStatusChange, User


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email")


class TaskSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ["id", "title", "description", "priority", "completed", "status", "user", "created_date"]
        read_only_fields = ("id", "user", "created_date")


class TaskStatusChangeSerializer(ModelSerializer):
    user = UserSerializer()
    task = TaskSerializer()

    class Meta:
        model = TaskStatusChange
        fields = ["id", "task", "original_status", "updated_status", "changed_date", "user"]
