from flask import Blueprint, jsonify, request

from app.api.errors import APIError
from app.services.common import parse_id, parse_positive_number
from app.decision.service import recommend

decision_bp = Blueprint("decision", __name__, url_prefix="/api/decision")


@decision_bp.post("/recommend")
def post_recommendation():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise APIError("A valid JSON object is required.")
    species_id = parse_id(payload.get("species_id"), "species_id")
    quantity_kg = parse_positive_number(payload.get("quantity_kg"), "quantity_kg")
    current_harbour_id = payload.get("current_harbour_id")
    if current_harbour_id is not None:
        current_harbour_id = parse_id(current_harbour_id, "current_harbour_id")
    return jsonify(recommend(species_id, quantity_kg, current_harbour_id))
