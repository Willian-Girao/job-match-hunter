import logging
import traceback
from job_match_hunter.data_layer.database import supabase_backend

# Use a logger named like the module itself.
logger = logging.getLogger(__name__)

def log_error(error: Exception, stage: str, request_id: str) -> None:
    """Record an application error.

    Logs the error to the application database.

    Args:
        error: Raised exception caught by the global error handler.
        stage: The URL path of the request.
        request_id: Random UUID.
    """
    # Formats stack trace and exception information.
    # `format_exception()` returns a list of strings each ending in new line.
    error_traceback = "".join(
        traceback.format_exception(error)
    )

    # Log error message.
    logger.error(
        "Request %s failed at %s",
        request_id,
        stage,
        exc_info=(type(error), error, error.__traceback__),
    )

    # Log error into Supabase.
    try:
        supabase_backend.table("error_logs").insert({
            "request_id": request_id,
            "stage": stage,
            "error_type": type(error).__name__,
            "message": str(error),
            "traceback": error_traceback,
        }).execute()
    except Exception:
        logger.exception(
            "Could not save error to Supabase for request %s",
            request_id,
        )