from flask import Blueprint, jsonify, request

from app.api.auth import require_session
from app.api.query import limit_arg, optional_id
from app.services.catalog_service import auction_detail, list_auctions
from app.services.mutation_service import close_auction, create_auction, place_bid

auction_bp = Blueprint("auctions", __name__, url_prefix="/api/auctions")


@auction_bp.get("")
def get_auctions():
    return jsonify({"auctions": list_auctions(
        harbour_id=optional_id(request.args, "harbour_id"),
        status=request.args.get("status"),
        limit=limit_arg(request.args),
    )})


@auction_bp.get("/<int:auction_id>")
def get_auction(auction_id):
    return jsonify({"auction": auction_detail(auction_id)})


@auction_bp.post("")
@require_session
def post_auction():
    return jsonify({"auction": create_auction(request.get_json(silent=True))}), 201


@auction_bp.post("/<int:auction_id>/bids")
@require_session
def post_bid(auction_id):
    return jsonify(place_bid(auction_id, request.get_json(silent=True))), 201


@auction_bp.post("/<int:auction_id>/close")
@require_session
def post_close_auction(auction_id):
    return jsonify({"auction": close_auction(auction_id)})
