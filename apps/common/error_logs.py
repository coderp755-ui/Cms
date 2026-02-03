from django.db import models
from apps.acounts.models import User


class ErrorLog(models.Model):
    """
    Model to store error logs for debugging and monitoring.
    """

    error_message = models.TextField()
    model_name = models.CharField(max_length=100, blank=True, null=True)
    api = models.CharField(max_length=200, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "error_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Error in {self.model_name or 'Unknown'} - {self.created_at}"


def log_error(
    exception: Exception, model_name: str, user: User = None, api: str = None
) -> None:
    """
    Logs an error to the ErrorLog model without interrupting execution.

    Args:
        exception (Exception): The exception instance to log.
        model_name (str): Name of the model where error occurred.
        user (User, optional): User associated with the error.
        api (str, optional): API endpoint where error occurred.
    """
    try:
        ErrorLog.objects.create(
            error_message=str(exception), model_name=model_name, api=api, user=user
        )
    except Exception as log_exc:
        print(f"Failed to log error: {log_exc}")
