import sys
import time
import django
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Avg, Count
from .models import SystemLog
from .serializers import SystemLogSerializer
from .buffer import get_buffer_logs, clear_buffer, add_to_buffer, SERVER_START_TIME


class SystemLogListView(APIView):
    def get(self, request):
        level = request.query_params.get('level')
        search = request.query_params.get('search')
        status_code = request.query_params.get('status_code')
        method = request.query_params.get('method')
        limit = int(request.query_params.get('limit', 100))
        limit = min(max(1, limit), 300)

        # Automatically purge expired logs based on configured retention policy
        auto_prune_expired_logs()

        logs_data = []
        total_count = 0
        error_count = 0
        warning_count = 0
        request_count = 0
        avg_duration = 0.0

        try:
            queryset = SystemLog.objects.exclude(Q(path__startswith='/api/logs') & (Q(status_code__isnull=True) | Q(status_code__lt=400)))

            # Global counts for KPI counters
            total_count = queryset.count()
            error_count = queryset.filter(Q(level__in=['ERROR', 'CRITICAL']) | Q(status_code__gte=500)).count()
            warning_count = queryset.filter(Q(level='WARNING') | Q(status_code__gte=400, status_code__lt=500)).count()
            request_count = queryset.filter(level__in=['REQUEST', 'INFO']).count()
            
            avg_res = queryset.filter(duration_ms__isnull=False).aggregate(avg=Avg('duration_ms'))['avg']
            avg_duration = round(float(avg_res), 1) if avg_res else 0.0

            # Apply filters
            if level and level.lower() != 'all':
                if level.upper() == 'ERROR':
                    queryset = queryset.filter(Q(level__in=['ERROR', 'CRITICAL']) | Q(status_code__gte=500))
                elif level.upper() == 'WARNING':
                    queryset = queryset.filter(Q(level='WARNING') | Q(status_code__gte=400, status_code__lt=500))
                elif level.upper() == 'REQUEST':
                    queryset = queryset.filter(level='REQUEST')
                elif level.upper() == 'INFO':
                    queryset = queryset.filter(level='INFO')
                else:
                    queryset = queryset.filter(level__iexact=level)

            if status_code and status_code.lower() != 'all':
                try:
                    sc = int(status_code)
                    queryset = queryset.filter(status_code=sc)
                except ValueError:
                    if status_code == '5xx':
                        queryset = queryset.filter(status_code__gte=500)
                    elif status_code == '4xx':
                        queryset = queryset.filter(status_code__gte=400, status_code__lt=500)
                    elif status_code == '2xx':
                        queryset = queryset.filter(status_code__gte=200, status_code__lt=300)

            if method and method.lower() != 'all':
                queryset = queryset.filter(method__iexact=method)

            if search:
                s = search.strip()
                queryset = queryset.filter(
                    Q(path__icontains=s) |
                    Q(message__icontains=s) |
                    Q(traceback__icontains=s) |
                    Q(ip_address__icontains=s) |
                    Q(source__icontains=s)
                )

            logs_slice = queryset[:limit]
            serializer = SystemLogSerializer(logs_slice, many=True)
            logs_data = serializer.data

        except Exception as err:
            # Fallback to in-memory buffer if DB is inaccessible
            buffer_items = get_buffer_logs(limit=limit, level=level, search=search, status_code=status_code)
            logs_data = buffer_items
            total_count = len(buffer_items)
            error_count = sum(1 for b in buffer_items if b.get('level') == 'ERROR' or (b.get('status_code') or 0) >= 500)
            warning_count = sum(1 for b in buffer_items if b.get('level') == 'WARNING' or 400 <= (b.get('status_code') or 0) < 500)
            request_count = sum(1 for b in buffer_items if b.get('level') in ('REQUEST', 'INFO'))

        # If DB logs are fewer than in-memory logs (e.g. startup logs before migrations), supplement with buffer
        if len(logs_data) < 10:
            buffer_items = get_buffer_logs(limit=limit, level=level, search=search, status_code=status_code)
            seen_ids = {str(l.get('id')) for l in logs_data}
            for b in buffer_items:
                if str(b.get('id')) not in seen_ids:
                    logs_data.append(b)

        uptime_secs = int(time.time() - SERVER_START_TIME)

        from .models import LogRetentionSetting
        setting = LogRetentionSetting.get_setting()

        return Response({
            "logs": logs_data,
            "metrics": {
                "total_logs": total_count or len(logs_data),
                "error_count": error_count,
                "warning_count": warning_count,
                "request_count": request_count,
                "avg_duration_ms": avg_duration,
                "uptime_seconds": uptime_secs,
                "server_status": "Degraded" if error_count > 5 else "Operational",
                "python_version": sys.version.split()[0],
                "django_version": django.get_version(),
                "retention_days": setting.retention_days,
                "is_auto_delete_enabled": setting.is_auto_delete_enabled,
                "last_cleaned_at": setting.last_cleaned_at,
            }
        })

    def delete(self, request):
        try:
            SystemLog.objects.all().delete()
        except Exception:
            pass
        clear_buffer()
        return Response({"success": True, "message": "All system logs cleared successfully."})


class ClearLogsView(APIView):
    def post(self, request):
        try:
            SystemLog.objects.all().delete()
        except Exception:
            pass
        clear_buffer()
        return Response({"success": True, "message": "All system logs cleared successfully."})


class GenerateTestLogView(APIView):
    def post(self, request):
        level = request.data.get('level', 'INFO').upper()
        msg = request.data.get('message', f"Test {level} log triggered from Admin Dashboard")
        tb = None
        status_code = 200

        if level == 'ERROR':
            status_code = 500
            tb = """Traceback (most recent call last):
  File "apps/orders/views.py", line 42, in process_order
    raise ValueError("Sample simulated production exception for log verification")
ValueError: Sample simulated production exception for log verification"""
        elif level == 'WARNING':
            status_code = 404

        log_dict = {
            "level": level,
            "source": "admin.diagnostics",
            "method": "POST",
            "path": "/api/logs/test/",
            "status_code": status_code,
            "ip_address": request.META.get('REMOTE_ADDR', '127.0.0.1'),
            "user_agent": request.META.get('HTTP_USER_AGENT', 'Kawaii Subete Admin UI'),
            "duration_ms": 14.2,
            "message": msg,
            "details": {"test": True, "triggered_by": "admin"},
            "traceback": tb,
        }

        add_to_buffer(log_dict)
        try:
            SystemLog.objects.create(
                level=level,
                source="admin.diagnostics",
                method="POST",
                path="/api/logs/test/",
                status_code=status_code,
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
                user_agent=request.META.get('HTTP_USER_AGENT', 'Kawaii Subete Admin UI'),
                duration_ms=14.2,
                message=msg,
                details={"test": True, "triggered_by": "admin"},
                traceback=tb,
            )
        except Exception:
            pass

        return Response({"success": True, "message": f"Created test {level} log."})


def auto_prune_expired_logs():
    """Prunes logs older than the configured retention_days."""
    try:
        from datetime import timedelta
        from django.utils import timezone
        from .models import LogRetentionSetting

        setting = LogRetentionSetting.get_setting()
        if setting.is_auto_delete_enabled and setting.retention_days > 0:
            cutoff = timezone.now() - timedelta(days=setting.retention_days)
            deleted, _ = SystemLog.objects.filter(created_at__lt=cutoff).delete()
            setting.last_cleaned_at = timezone.now()
            setting.save(update_fields=['last_cleaned_at'])
            return deleted
    except Exception:
        pass
    return 0


class LogRetentionView(APIView):
    def get(self, request):
        from .models import LogRetentionSetting
        setting = LogRetentionSetting.get_setting()
        return Response({
            "retention_days": setting.retention_days,
            "is_auto_delete_enabled": setting.is_auto_delete_enabled,
            "last_cleaned_at": setting.last_cleaned_at,
        })

    def post(self, request):
        from .models import LogRetentionSetting
        setting = LogRetentionSetting.get_setting()
        
        retention_days = request.data.get('retention_days')
        is_auto_delete_enabled = request.data.get('is_auto_delete_enabled')

        if retention_days is not None:
            try:
                setting.retention_days = max(0, int(retention_days))
            except ValueError:
                pass

        if is_auto_delete_enabled is not None:
            setting.is_auto_delete_enabled = bool(is_auto_delete_enabled)

        setting.save()

        # Run auto-pruning immediately with new setting
        pruned_count = auto_prune_expired_logs()

        return Response({
            "success": True,
            "message": f"Log retention policy updated to {setting.retention_days} day(s).",
            "retention_days": setting.retention_days,
            "is_auto_delete_enabled": setting.is_auto_delete_enabled,
            "last_cleaned_at": setting.last_cleaned_at,
            "pruned_count": pruned_count,
        })


class PruneLogsView(APIView):
    def post(self, request):
        days = request.data.get('days')
        from datetime import timedelta
        from django.utils import timezone
        from .models import LogRetentionSetting

        try:
            days_val = int(days) if days is not None else LogRetentionSetting.get_setting().retention_days
            cutoff = timezone.now() - timedelta(days=max(1, days_val))
            deleted, _ = SystemLog.objects.filter(created_at__lt=cutoff).delete()
            
            setting = LogRetentionSetting.get_setting()
            setting.last_cleaned_at = timezone.now()
            setting.save(update_fields=['last_cleaned_at'])

            return Response({
                "success": True,
                "deleted_count": deleted,
                "message": f"Deleted {deleted} log(s) older than {days_val} day(s)."
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

