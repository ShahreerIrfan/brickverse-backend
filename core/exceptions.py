import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    """DRF's default handler, plus: an unexpected error on a product write
    returns JSON naming the error instead of a blank HTML 500 page, so the
    admin form can show why a save failed (and the traceback is logged)."""
    response = exception_handler(exc, context)
    if response is not None:
        return response

    request = context.get("request")
    logger.exception("Unhandled error in %s %s", getattr(request, "method", "?"), getattr(request, "path", "?"))
    if (
        request is not None
        and request.method in ("POST", "PUT", "PATCH", "DELETE")
        and request.path.startswith("/api/products/")
    ):
        return Response({"error": f"{type(exc).__name__}: {str(exc)[:300]}"}, status=500)
    return None
