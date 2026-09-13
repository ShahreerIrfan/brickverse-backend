import time
import traceback
import json
from .models import SystemLog
from .buffer import add_to_buffer


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        request._logging_start_time = start_time
        
        response = self.get_response(request)
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        self.record_log(request, response, duration_ms)
        
        return response

    def process_exception(self, request, exception):
        duration_ms = 0
        if hasattr(request, '_logging_start_time'):
            duration_ms = round((time.time() - request._logging_start_time) * 1000, 2)
            
        tb_str = traceback.format_exc()
        self.record_log(
            request=request,
            response=None,
            duration_ms=duration_ms,
            exception=exception,
            traceback_text=tb_str,
            status_code=500,
        )
        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')

    def record_log(self, request, response=None, duration_ms=0, exception=None, traceback_text=None, status_code=None):
        try:
            path = request.path
            # Skip noise like favicon, static files, and self-polling on /api/logs/
            if (path in ('/favicon.ico', '/robots.txt') or path.startswith('/api/logs/')) and (not response or response.status_code < 400):
                return

            status = status_code or (response.status_code if response else 500)
            method = request.method
            ip = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            # Determine log level
            if exception or status >= 500:
                level = 'ERROR'
            elif status >= 400:
                level = 'WARNING'
            else:
                level = 'REQUEST'

            # Message
            if exception:
                message = f"{type(exception).__name__}: {str(exception)}"
            else:
                message = f"{method} {path} completed with {status} in {duration_ms}ms"

            details = {
                "query_params": dict(request.GET.items()),
                "content_type": request.META.get('CONTENT_TYPE', ''),
            }

            log_dict = {
                "level": level,
                "source": "django.request",
                "method": method,
                "path": path,
                "status_code": status,
                "ip_address": ip,
                "user_agent": user_agent[:200] if user_agent else "",
                "duration_ms": duration_ms,
                "message": message,
                "details": details,
                "traceback": traceback_text,
            }

            # Always add to memory buffer for instantaneous real-time visibility
            add_to_buffer(log_dict)

            # Persist to database
            try:
                SystemLog.objects.create(
                    level=level,
                    source='django.request',
                    method=method,
                    path=path,
                    status_code=status,
                    ip_address=ip,
                    user_agent=user_agent,
                    duration_ms=duration_ms,
                    message=message,
                    details=details,
                    traceback=traceback_text,
                )
            except Exception as db_err:
                # If database write fails (e.g. during migrations or DB down), buffer still holds it
                add_to_buffer({
                    "level": "ERROR",
                    "source": "django.db",
                    "method": "DB_WRITE",
                    "path": "/db/system_log",
                    "status_code": 500,
                    "ip_address": ip,
                    "duration_ms": 0,
                    "message": f"Database logging failed: {str(db_err)}",
                    "details": {},
                    "traceback": traceback.format_exc(),
                })
        except Exception:
            pass
