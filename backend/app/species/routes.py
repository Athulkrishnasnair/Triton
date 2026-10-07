from flask import Blueprint, jsonify

from app.services.market_service import list_species

species_bp = Blueprint("species", __name__, url_prefix="/api/species")


@species_bp.get("")
def get_species():
    return jsonify({"species": list_species()})
