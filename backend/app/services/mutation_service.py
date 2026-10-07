"""Validated, transactional MVP write operations."""

from datetime import datetime, timezone

from sqlalchemy import desc

from app.api.errors import APIError
from app.api.serialization import (
    provenance,
    serialize_alert,
    serialize_announcement,
    serialize_auction,
    serialize_demand,
    serialize_ice,
    serialize_storage,
)
from app.extensions import db
from app.models import (
    Announcement,
    Auction,
    AuctionBid,
    Buyer,
    BuyerDemand,
    ColdStorage,
    FishSpecies,
    Harbour,
    HarbourAlert,
    IcePlant,
    utcnow,
)
from app.services.common import parse_id, parse_positive_number


def _object(payload):
    if not isinstance(payload, dict):
        raise APIError("A valid JSON object is required.")
    return payload


def _get(model, identifier, label):
    row = db.session.get(model, identifier)
    if row is None:
        raise APIError(f"{label} not found.", 404, "not_found")
    return row


def _optional_text(payload, key, allowed, default):
    value = payload.get(key, default)
    if not isinstance(value, str) or value.upper() not in allowed:
        raise APIError(f"{key} must be one of: {', '.join(sorted(allowed))}.")
    return value.upper()


def _parse_datetime(value, field):
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise APIError(f"{field} must be an ISO 8601 datetime.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise APIError(f"{field} must be an ISO 8601 datetime.") from None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def create_auction(payload):
    payload = _object(payload)
    harbour_id = parse_id(payload.get("harbour_id"), "harbour_id")
    species_id = parse_id(payload.get("species_id"), "species_id")
    harbour = _get(Harbour, harbour_id, "Harbour")
    species = _get(FishSpecies, species_id, "Fish species")
    quantity = parse_positive_number(payload.get("quantity_kg"), "quantity_kg")
    starting_price = parse_positive_number(payload.get("starting_price"), "starting_price")
    grade = payload.get("quality_grade", "A")
    if not isinstance(grade, str) or grade not in {"A", "B", "C"}:
        raise APIError("quality_grade must be A, B, or C.")
    now = utcnow()
    auction = Auction(
        harbour=harbour,
        species=species,
        quantity_kg=quantity,
        quality_grade=grade,
        starting_price=starting_price,
        current_price=starting_price,
        status="LIVE",
        started_at=now,
        created_at=now,
        recorded_at=now,
        source="AUCTION_OPERATOR",
        confidence=1.0,
    )
    db.session.add(auction)
    _commit()
    return serialize_auction(auction, include_bids=True)


def place_bid(auction_id, payload):
    payload = _object(payload)
    auction = _get(Auction, auction_id, "Auction")
    if auction.status != "LIVE":
        raise APIError("Bids can only be placed on live auctions.", 409, "conflict")
    buyer_id = parse_id(payload.get("buyer_id"), "buyer_id")
    buyer = _get(Buyer, buyer_id, "Buyer")
    if buyer.status != "ACTIVE":
        raise APIError("Buyer is not active.", 409, "conflict")
    amount = parse_positive_number(payload.get("amount"), "amount")
    if amount <= auction.current_price:
        raise APIError("Bid must be higher than the current price.", 400, "invalid_bid")
    bid = AuctionBid(
        auction=auction,
        buyer=buyer,
        amount=amount,
        timestamp=utcnow(),
    )
    auction.current_price = amount
    auction.recorded_at = bid.timestamp
    auction.source = "AUCTION_OPERATOR"
    auction.confidence = 1.0
    db.session.add(bid)
    _commit()
    return {
        "auction": serialize_auction(auction, include_bids=True),
        "bid": {
            "id": bid.id,
            "buyer_id": bid.buyer_id,
            "amount": bid.amount,
            "timestamp": bid.timestamp.isoformat() + "Z",
            **provenance(bid.timestamp, auction.source, auction.confidence),
        },
    }


def close_auction(auction_id):
    auction = _get(Auction, auction_id, "Auction")
    if auction.status != "LIVE":
        raise APIError("Only a live auction can be closed.", 409, "conflict")
    winning_bid = AuctionBid.query.filter_by(auction_id=auction.id).order_by(
        desc(AuctionBid.amount), AuctionBid.timestamp.asc(), AuctionBid.id.asc()
    ).first()
    now = utcnow()
    auction.status = "CLOSED"
    auction.closed_at = now
    auction.recorded_at = now
    auction.source = "AUCTION_OPERATOR"
    auction.confidence = 1.0
    if winning_bid:
        auction.winner_id = winning_bid.buyer_id
        auction.current_price = winning_bid.amount
    _commit()
    return serialize_auction(auction, include_bids=True)


def create_buyer_demand(buyer_id, payload):
    payload = _object(payload)
    buyer = _get(Buyer, buyer_id, "Buyer")
    species_id = parse_id(payload.get("species_id"), "species_id")
    species = _get(FishSpecies, species_id, "Fish species")
    requested = parse_positive_number(payload.get("requested_quantity_kg"), "requested_quantity_kg")
    priority = _optional_text(payload, "priority", {"LOW", "NORMAL", "HIGH", "URGENT"}, "NORMAL")
    now = utcnow()
    demand = BuyerDemand(
        buyer=buyer,
        species=species,
        requested_quantity_kg=requested,
        fulfilled_quantity_kg=0,
        priority=priority,
        status="OPEN",
        source="BUYER_REPORTED",
        recorded_at=now,
        confidence=1.0,
        updated_at=now,
    )
    db.session.add(demand)
    _commit()
    return serialize_demand(demand)


def update_buyer_demand(demand_id, payload):
    payload = _object(payload)
    demand = _get(BuyerDemand, demand_id, "Buyer demand")
    allowed_fields = {"requested_quantity_kg", "fulfilled_quantity_kg", "priority", "status"}
    if not payload or set(payload) - allowed_fields:
        raise APIError("Provide one or more supported buyer demand fields.")
    requested = demand.requested_quantity_kg
    fulfilled = demand.fulfilled_quantity_kg
    if "requested_quantity_kg" in payload:
        requested = parse_positive_number(payload["requested_quantity_kg"], "requested_quantity_kg")
    if "fulfilled_quantity_kg" in payload:
        try:
            fulfilled = float(payload["fulfilled_quantity_kg"])
        except (TypeError, ValueError):
            raise APIError("fulfilled_quantity_kg must be a non-negative number.") from None
        if not 0 <= fulfilled < float("inf"):
            raise APIError("fulfilled_quantity_kg must be a non-negative finite number.")
    if fulfilled > requested:
        raise APIError("fulfilled_quantity_kg cannot exceed requested_quantity_kg.")
    if "priority" in payload:
        demand.priority = _optional_text(
            payload, "priority", {"LOW", "NORMAL", "HIGH", "URGENT"}, demand.priority
        )
    requested_status = payload.get("status")
    if requested_status is not None and (
        not isinstance(requested_status, str)
        or requested_status not in {"OPEN", "PARTIAL", "FULFILLED", "CANCELLED"}
    ):
        raise APIError("status must be OPEN, PARTIAL, FULFILLED, or CANCELLED.")
    if requested_status == "CANCELLED":
        demand.status = "CANCELLED"
    else:
        demand.status = "FULFILLED" if fulfilled == requested else ("PARTIAL" if fulfilled > 0 else "OPEN")
    demand.requested_quantity_kg = requested
    demand.fulfilled_quantity_kg = fulfilled
    demand.source = "BUYER_REPORTED"
    demand.confidence = 1.0
    demand.recorded_at = utcnow()
    demand.updated_at = demand.recorded_at
    _commit()
    return serialize_demand(demand)


def update_ice(harbour_id, payload):
    payload = _object(payload)
    ice = IcePlant.query.filter_by(harbour_id=harbour_id).first()
    if ice is None:
        raise APIError("Ice plant not found for this harbour.", 404, "not_found")
    allowed = {"capacity_tonnes", "available_tonnes", "price_per_kg", "queue_count", "status"}
    if not payload or set(payload) - allowed:
        raise APIError("Provide one or more supported ice plant fields.")
    values = {
        "capacity_tonnes": ice.capacity_tonnes,
        "available_tonnes": ice.available_tonnes,
        "price_per_kg": ice.price_per_kg,
        "queue_count": ice.queue_count,
    }
    for field in set(payload) & set(values):
        raw = payload[field]
        if field == "queue_count":
            if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
                raise APIError("queue_count must be a non-negative integer.")
            values[field] = raw
        else:
            try:
                number = float(raw)
            except (TypeError, ValueError):
                raise APIError(f"{field} must be a non-negative number.") from None
            if number < 0 or number == float("inf") or number != number:
                raise APIError(f"{field} must be a non-negative finite number.")
            values[field] = number
    if values["available_tonnes"] > values["capacity_tonnes"]:
        raise APIError("available_tonnes cannot exceed capacity_tonnes.")
    for field, value in values.items():
        setattr(ice, field, value)
    if "status" in payload:
        ice.status = _optional_text(payload, "status", {"AVAILABLE", "LIMITED", "CLOSED"}, ice.status)
    ice.source = "HARBOUR_OPERATOR"
    ice.confidence = 1.0
    ice.recorded_at = utcnow()
    ice.updated_at = ice.recorded_at
    _commit()
    return serialize_ice(ice)


def update_storage(harbour_id, payload):
    payload = _object(payload)
    storage = ColdStorage.query.filter_by(harbour_id=harbour_id).first()
    if storage is None:
        raise APIError("Cold storage not found for this harbour.", 404, "not_found")
    allowed = {"capacity_tonnes", "occupied_tonnes", "reserved_tonnes", "expected_release", "status"}
    if not payload or set(payload) - allowed:
        raise APIError("Provide one or more supported cold storage fields.")
    values = {
        "capacity_tonnes": storage.capacity_tonnes,
        "occupied_tonnes": storage.occupied_tonnes,
        "reserved_tonnes": storage.reserved_tonnes,
    }
    for field in values:
        if field in payload:
            try:
                number = float(payload[field])
            except (TypeError, ValueError):
                raise APIError(f"{field} must be a non-negative number.") from None
            if number < 0 or number == float("inf") or number != number:
                raise APIError(f"{field} must be a non-negative finite number.")
            values[field] = number
    if values["occupied_tonnes"] + values["reserved_tonnes"] > values["capacity_tonnes"]:
        raise APIError("occupied_tonnes plus reserved_tonnes cannot exceed capacity_tonnes.")
    for field, value in values.items():
        setattr(storage, field, value)
    if "expected_release" in payload:
        storage.expected_release = _parse_datetime(payload["expected_release"], "expected_release")
    if "status" in payload:
        storage.status = _optional_text(payload, "status", {"AVAILABLE", "LIMITED", "FULL", "CLOSED"}, storage.status)
    storage.source = "HARBOUR_OPERATOR"
    storage.confidence = 1.0
    storage.recorded_at = utcnow()
    storage.updated_at = storage.recorded_at
    _commit()
    return serialize_storage(storage)


def create_announcement(payload):
    payload = _object(payload)
    harbour_id = payload.get("harbour_id")
    harbour = _get(Harbour, parse_id(harbour_id, "harbour_id"), "Harbour") if harbour_id is not None else None
    title = payload.get("title")
    message = payload.get("message")
    if not isinstance(title, str) or not title.strip() or len(title) > 200:
        raise APIError("title must be a non-empty string of 200 characters or fewer.")
    if not isinstance(message, str) or not message.strip():
        raise APIError("message must be a non-empty string.")
    priority = _optional_text(payload, "priority", {"LOW", "NORMAL", "HIGH", "URGENT"}, "NORMAL")
    now = utcnow()
    expires_at = _parse_datetime(payload.get("expires_at"), "expires_at")
    if expires_at and expires_at <= now:
        raise APIError("expires_at must be in the future.")
    announcement = Announcement(
        harbour=harbour,
        title=title.strip(),
        message=message.strip(),
        priority=priority,
        published_at=now,
        expires_at=expires_at,
        source="HARBOUR_OPERATOR",
        created_at=now,
    )
    db.session.add(announcement)
    _commit()
    return serialize_announcement(announcement)


def create_alert(payload):
    payload = _object(payload)
    harbour_id = parse_id(payload.get("harbour_id"), "harbour_id")
    harbour = _get(Harbour, harbour_id, "Harbour")
    alert_type = payload.get("type")
    title = payload.get("title")
    message = payload.get("message")
    if not isinstance(alert_type, str) or not alert_type.strip() or len(alert_type) > 40:
        raise APIError("type must be a non-empty string of 40 characters or fewer.")
    if not isinstance(title, str) or not title.strip() or len(title) > 200:
        raise APIError("title must be a non-empty string of 200 characters or fewer.")
    if not isinstance(message, str) or not message.strip():
        raise APIError("message must be a non-empty string.")
    severity = _optional_text(payload, "severity", {"INFO", "WARNING", "CRITICAL"}, "INFO")
    expires_at = _parse_datetime(payload.get("expires_at"), "expires_at")
    now = utcnow()
    if expires_at and expires_at <= now:
        raise APIError("expires_at must be in the future.")
    alert = HarbourAlert(
        harbour=harbour,
        type=alert_type.strip().upper(),
        title=title.strip(),
        message=message.strip(),
        severity=severity,
        active=True,
        created_at=now,
        expires_at=expires_at,
        source="HARBOUR_OPERATOR",
    )
    db.session.add(alert)
    _commit()
    return serialize_alert(alert)
