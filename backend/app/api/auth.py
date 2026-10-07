from functools import wraps

from flask import current_app, request, session

from app.api.errors import APIError
from app.extensions import db
from app.models import User


def require_session(view):
    """Require a valid user session and reject cross-origin browser writes."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id or db.session.get(User, user_id) is None:
            session.pop("user_id", None)
            raise APIError("Authentication required.", 401, "unauthorized")
        origin = request.headers.get("Origin")
        if not origin or origin not in current_app.config["CORS_ORIGINS"]:
            raise APIError("Request origin is not allowed.", 403, "forbidden")
        return view(*args, **kwargs)
    return wrapped
