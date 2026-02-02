from apps.users.models import ErrorLog, Users

def log_error(exception: Exception, model_name: str, user: Users = None, api: str = None) -> None:
    """
    Logs an error to the ErrorLog model without interrupting execution.

    Args:
        exception (Exception): The exception instance to log.
        context (dict): Additional context information about the error.
        user (User, optional): User associated with the error.
    """
    try:
        ErrorLog.objects.create(
            error_message=str(exception),
            model_name=model_name,
            api=api,
            user=user
        )
    except Exception as log_exc:
        print(f"Failed to log error: {log_exc}")