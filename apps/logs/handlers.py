import logging
import traceback
from .buffer import add_to_buffer


class DBLogHandler(logging.Handler):
    """
    Captures Python logging events (e.g. logger.error, unhandled DB errors, Celery/Worker logs)
    and sends them to the in-memory ring buffer and SystemLog DB table.
    """
    def emit(self, record):
        try:
            from .models import SystemLog
            level = record.levelname
            msg = self.format(record)
            
            tb_str = None
            if record.exc_info:
                tb_str = "".join(traceback.format_exception(*record.exc_info))

            log_dict = {
                "level": level if level in ('ERROR', 'WARNING', 'CRITICAL') else 'INFO',
                "source": record.name,
                "method": getattr(record, 'method', 'SYS'),
                "path": getattr(record, 'path', ''),
                "status_code": getattr(record, 'status_code', None),
                "ip_address": getattr(record, 'ip_address', 'server'),
                "user_agent": "",
                "duration_ms": 0,
                "message": msg,
                "details": {
                    "filename": record.filename,
                    "lineno": record.lineno,
                    "funcName": record.funcName,
                },
                "traceback": tb_str,
            }

            add_to_buffer(log_dict)

            try:
                SystemLog.objects.create(
                    level=log_dict["level"],
                    source=record.name,
                    method=log_dict["method"],
                    path=log_dict["path"],
                    status_code=log_dict["status_code"],
                    ip_address=log_dict["ip_address"],
                    message=msg,
                    details=log_dict["details"],
                    traceback=tb_str,
                )
            except Exception:
                pass
        except Exception:
            pass
