from functools import wraps
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from .models import AuditLog

def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return (forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR"))

def audit(request, action, entity, entity_id="", metadata=None):
    safe_metadata = metadata or {}
    AuditLog.objects.create(
        actor=request.user if getattr(request.user, "is_authenticated", False) else None,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        metadata=safe_metadata,
        ip_address=client_ip(request),
    )

def roles_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/login/?next={request.path}")
            if request.user.role not in roles and not request.user.is_superuser:
                messages.error(request, "Your role cannot perform that action.")
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
