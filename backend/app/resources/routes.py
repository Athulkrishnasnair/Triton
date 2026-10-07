from flask import Blueprint, jsonify
from flask import request

from app.api.auth import require_session
from app.services.catalog_service import harbour_resources
from app.services.mutation_service import update_ice, update_storage

resources_bp = Blueprint("resources", __name__, url_prefix="/api/resources")


@resources_bp.get("/<int:harbour_id>")
def get_resources(harbour_id):
    return jsonify(harbour_resources(harbour_id))


@resources_bp.patch("/<int:harbour_id>/ice")
@require_session
def patch_ice(harbour_id):
    return jsonify({"ice": update_ice(harbour_id, request.get_json(silent=True))})


@resources_bp.patch("/<int:harbour_id>/storage")
@require_session
def patch_storage(harbour_id):
    return jsonify({"cold_storage": update_storage(harbour_id, request.get_json(silent=True))})
