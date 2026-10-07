from app.api.errors import APIError
from app.api.serialization import (
    serialize_alert,
    serialize_announcement,
    serialize_auction,
    serialize_buyer,
    serialize_demand,
    serialize_harbour,
    serialize_ice,
    serialize_storage,
)
from app.extensions import db
from app.models import (
    Announcement,
    Auction,
    Buyer,
    BuyerDemand,
    ColdStorage,
    Harbour,
    HarbourAlert,
    IcePlant,
    utcnow,
)
from app.services.common import get_harbour_or_404


def list_harbours():
    return [serialize_harbour(item) for item in Harbour.query.order_by(Harbour.name).all()]


def harbour_detail(harbour_id):
    return serialize_harbour(get_harbour_or_404(harbour_id))


def list_buyers(harbour_id=None, limit=100):
    query = Buyer.query
    if harbour_id is not None:
        harbour = get_harbour_or_404(harbour_id)
        query = query.filter(db.func.lower(Buyer.location).contains(harbour.name.lower()))
    return [serialize_buyer(item) for item in query.order_by(Buyer.name).limit(limit).all()]


def buyer_detail(buyer_id):
    buyer = db.session.get(Buyer, buyer_id)
    if buyer is None:
        raise APIError("Buyer not found.", 404, "not_found")
    return serialize_buyer(buyer)


def buyer_demand(buyer_id, limit=100):
    buyer = db.session.get(Buyer, buyer_id)
    if buyer is None:
        raise APIError("Buyer not found.", 404, "not_found")
    demands = BuyerDemand.query.filter_by(buyer_id=buyer.id).order_by(
        BuyerDemand.updated_at.desc(), BuyerDemand.id.desc()
    ).limit(limit).all()
    return {"buyer": serialize_buyer(buyer), "demand": [serialize_demand(item) for item in demands]}


def harbour_resources(harbour_id):
    harbour = get_harbour_or_404(harbour_id)
    ice = IcePlant.query.filter_by(harbour_id=harbour.id).first()
    storage = ColdStorage.query.filter_by(harbour_id=harbour.id).first()
    return {
        "harbour": serialize_harbour(harbour),
        "ice": serialize_ice(ice),
        "cold_storage": serialize_storage(storage),
        "is_demo": bool((ice and ice.source == "DEMO") or (storage and storage.source == "DEMO")),
        "is_demo_data": bool((ice and ice.source == "DEMO") or (storage and storage.source == "DEMO")),
    }


def list_auctions(harbour_id=None, status=None, limit=100):
    query = Auction.query
    if harbour_id is not None:
        get_harbour_or_404(harbour_id)
        query = query.filter_by(harbour_id=harbour_id)
    if status:
        query = query.filter(db.func.upper(Auction.status) == status.upper())
    return [serialize_auction(item) for item in query.order_by(Auction.created_at.desc()).limit(limit).all()]


def auction_detail(auction_id):
    auction = db.session.get(Auction, auction_id)
    if auction is None:
        raise APIError("Auction not found.", 404, "not_found")
    return serialize_auction(auction, include_bids=True)


def list_announcements(harbour_id=None, limit=100):
    query = Announcement.query
    query = query.filter(db.or_(Announcement.expires_at.is_(None), Announcement.expires_at > utcnow()))
    if harbour_id is not None:
        harbour = get_harbour_or_404(harbour_id)
        query = query.filter(db.or_(Announcement.harbour_id == harbour.id, Announcement.harbour_id.is_(None)))
    return [
        serialize_announcement(item)
        for item in query.order_by(Announcement.published_at.desc()).limit(limit).all()
    ]


def list_alerts(harbour_id=None, active_only=True, limit=100):
    query = HarbourAlert.query
    if harbour_id is not None:
        get_harbour_or_404(harbour_id)
        query = query.filter_by(harbour_id=harbour_id)
    if active_only:
        query = query.filter_by(active=True)
        query = query.filter(db.or_(HarbourAlert.expires_at.is_(None), HarbourAlert.expires_at > utcnow()))
    return [serialize_alert(item) for item in query.order_by(HarbourAlert.created_at.desc()).limit(limit).all()]
