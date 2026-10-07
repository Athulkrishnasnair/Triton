from flask import Blueprint, jsonify, request

from app.api.query import limit_arg, optional_id
from app.services.common import parse_positive_number
from app.services.market_service import compare_markets, list_prices

market_bp = Blueprint("market", __name__, url_prefix="/api/market")


@market_bp.get("/prices")
def get_prices():
    return jsonify({"prices": list_prices(
        species_id=optional_id(request.args, "species_id"),
        harbour_id=optional_id(request.args, "harbour_id"),
        limit=limit_arg(request.args),
    )})


@market_bp.get("/compare")
def get_market_comparison():
    species_id = optional_id(request.args, "species_id")
    quantity_kg = parse_positive_number(request.args.get("quantity_kg"), "quantity_kg")
    if species_id is None:
        from app.api.errors import APIError
        raise APIError("species_id is required.")
    return jsonify(compare_markets(
        species_id,
        quantity_kg,
        optional_id(request.args, "harbour_id"),
    ))
