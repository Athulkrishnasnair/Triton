import math

from app.api.errors import APIError
from app.models import Harbour, FishSpecies


def parse_positive_number(value, field_name):
    if isinstance(value, bool):
        raise APIError(f"{field_name} must be a positive number.")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise APIError(f"{field_name} must be a positive number.") from None
    if not math.isfinite(number) or number <= 0:
        raise APIError(f"{field_name} must be a positive number.")
    return number


def parse_id(value, field_name):
    if isinstance(value, bool):
        raise APIError(f"{field_name} must be a valid integer.")
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise APIError(f"{field_name} must be a valid integer.") from None
    if parsed <= 0:
        raise APIError(f"{field_name} must be a valid positive integer.")
    return parsed


def get_harbour_or_404(harbour_id):
    harbour = db_get(Harbour, harbour_id)
    if harbour is None:
        raise APIError("Harbour not found.", 404, "not_found")
    return harbour


def get_species_or_404(species_id):
    species = db_get(FishSpecies, species_id)
    if species is None:
        raise APIError("Fish species not found.", 404, "not_found")
    return species


def db_get(model, identifier):
    from app.extensions import db
    return db.session.get(model, identifier)
