from django.urls import path
from .views import (
    SystemLogListView,
    ClearLogsView,
    GenerateTestLogView,
    LogRetentionView,
    PruneLogsView,
)

urlpatterns = [
    path('', SystemLogListView.as_view(), name='system-logs-list'),
    path('clear/', ClearLogsView.as_view(), name='system-logs-clear'),
    path('test/', GenerateTestLogView.as_view(), name='system-logs-test'),
    path('retention/', LogRetentionView.as_view(), name='system-logs-retention'),
    path('prune/', PruneLogsView.as_view(), name='system-logs-prune'),
]
