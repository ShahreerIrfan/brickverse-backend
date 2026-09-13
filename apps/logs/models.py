from django.db import models


class SystemLog(models.Model):
    LEVEL_CHOICES = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
        ('REQUEST', 'Request'),
    ]

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='INFO', db_index=True)
    source = models.CharField(max_length=120, default='django.request')
    method = models.CharField(max_length=15, blank=True, null=True, db_index=True)
    path = models.CharField(max_length=500, blank=True, null=True, db_index=True)
    status_code = models.IntegerField(null=True, blank=True, db_index=True)
    ip_address = models.CharField(max_length=100, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    duration_ms = models.FloatField(null=True, blank=True)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    traceback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'

    def __str__(self):
        status = f" [{self.status_code}]" if self.status_code else ""
        return f"[{self.level}] {self.method or ''} {self.path or ''}{status} - {self.message[:60]}"
