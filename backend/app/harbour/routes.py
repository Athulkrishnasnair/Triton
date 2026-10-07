from flask import Blueprint, jsonify

from app.services.catalog_service import harbour_detail, list_harbours
from app.services.market_service import harbour_changes, harbour_dashboard

harbour_bp = Blueprint("harbours", __name__, url_prefix="/api/harbours")


@harbour_bp.get("")
def get_harbours():
    return jsonify({"harbours": list_harbours()})


@harbour_bp.get("/<int:harbour_id>")
def get_harbour(harbour_id):
    return jsonify({"harbour": harbour_detail(harbour_id)})


@harbour_bp.get("/<int:harbour_id>/dashboard")
def get_harbour_dashboard(harbour_id):
    return jsonify(harbour_dashboard(harbour_id))


@harbour_bp.get("/<int:harbour_id>/changes")
def get_harbour_changes(harbour_id):
    return jsonify(harbour_changes(harbour_id))
