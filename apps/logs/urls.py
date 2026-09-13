from django.urls import path
from .views import SystemLogListView, ClearLogsView, GenerateTestLogView

urlpatterns = [
    path('', SystemLogListView.as_view(), name='system-logs-list'),
    path('clear/', ClearLogsView.as_view(), name='system-logs-clear'),
    path('test/', GenerateTestLogView.as_view(), name='system-logs-test'),
]
