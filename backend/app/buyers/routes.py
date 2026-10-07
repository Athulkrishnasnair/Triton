from flask import Blueprint, jsonify, request

from app.api.auth import require_session
from app.api.query import limit_arg, optional_id
from app.services.catalog_service import buyer_detail, buyer_demand, list_buyers
from app.services.mutation_service import create_buyer_demand, update_buyer_demand

buyers_bp = Blueprint("buyers", __name__, url_prefix="/api/buyers")


@buyers_bp.get("")
def get_buyers():
    return jsonify({"buyers": list_buyers(
        harbour_id=optional_id(request.args, "harbour_id"),
        limit=limit_arg(request.args),
    )})


@buyers_bp.get("/<int:buyer_id>")
def get_buyer(buyer_id):
    return jsonify({"buyer": buyer_detail(buyer_id)})


@buyers_bp.get("/<int:buyer_id>/demand")
def get_buyer_demand(buyer_id):
    return jsonify(buyer_demand(buyer_id, limit_arg(request.args)))


@buyers_bp.post("/<int:buyer_id>/demand")
@require_session
def post_buyer_demand(buyer_id):
    return jsonify({"demand": create_buyer_demand(
        buyer_id, request.get_json(silent=True)
    )}), 201


@buyers_bp.patch("/demand/<int:demand_id>")
@require_session
def patch_buyer_demand(demand_id):
    return jsonify({"demand": update_buyer_demand(
        demand_id, request.get_json(silent=True)
    )})
