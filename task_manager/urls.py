from django.contrib import admin
from django.urls import include, path
from tasks.views import (
    DeleteTaskView,
    UserLoginView,
    UserLogoutView,
    UserCreateView,
    PreferencesView,
    TaskView,
    TaskCreateView,
    UpdateTaskView,
    toggle_complete_task,
    index_page,
)
from rest_framework_nested import routers
from tasks.views import TaskStatusChangeViewAPI, TaskStatusChangeViewNestedAPI, TaskViewSetAPI

router = routers.SimpleRouter()

router.register("tasks", TaskViewSetAPI)

task_router = routers.NestedSimpleRouter(router, "tasks", lookup="task")
task_router.register("history", TaskStatusChangeViewNestedAPI)

router.register("history", TaskStatusChangeViewAPI)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("__reload__/", include("django_browser_reload.urls")),
    path("user/login/", UserLoginView.as_view()),
    path("user/logout/", UserLogoutView.as_view()),
    path("user/signup/", UserCreateView.as_view()),
    path("user/preferences/", PreferencesView.as_view()),
    path("tasks/", TaskView.as_view()),
    path("add_task/", TaskCreateView.as_view()),
    path("update_task/<int:pk>", UpdateTaskView.as_view()),
    path("delete_task/<int:pk>", DeleteTaskView.as_view()),
    path("toggle_complete_task/<int:pk>", toggle_complete_task),
    path("api/", include(router.urls)),
    path("api/", include(task_router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("", index_page),
]
