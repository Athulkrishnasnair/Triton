from flask import Blueprint, jsonify, request

from app.api.auth import require_session
from app.api.query import limit_arg, optional_id
from app.services.catalog_service import list_alerts, list_announcements
from app.services.mutation_service import create_alert, create_announcement

announcements_bp = Blueprint("announcements", __name__, url_prefix="/api/announcements")
alerts_bp = Blueprint("alerts", __name__, url_prefix="/api/alerts")


@announcements_bp.get("")
def get_announcements():
    return jsonify({"announcements": list_announcements(
        harbour_id=optional_id(request.args, "harbour_id"),
        limit=limit_arg(request.args),
    )})


@alerts_bp.get("")
def get_alerts():
    active_value = request.args.get("active", "true").lower()
    if active_value not in {"true", "false"}:
        from app.api.errors import APIError
        raise APIError("active must be true or false.")
    return jsonify({"alerts": list_alerts(
        harbour_id=optional_id(request.args, "harbour_id"),
        active_only=active_value == "true",
        limit=limit_arg(request.args),
    )})


@announcements_bp.post("")
@require_session
def post_announcement():
    return jsonify({"announcement": create_announcement(
        request.get_json(silent=True)
    )}), 201


@alerts_bp.post("")
@require_session
def post_alert():
    return jsonify({"alert": create_alert(request.get_json(silent=True))}), 201
