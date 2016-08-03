from django.db import models


class CronLog(models.Model):
    """A log of cron jobs."""
    command = models.CharField(max_length=256)
    message = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message

    class Meta:
        ordering = ['created_on', 'command']
        verbose_name = "Cron Log"
        verbose_name_plural = "Cron Logs"
