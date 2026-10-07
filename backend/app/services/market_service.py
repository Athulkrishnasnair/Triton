from sqlalchemy import desc

from app.api.serialization import (
    provenance,
    serialize_alert,
    serialize_announcement,
    serialize_auction,
    serialize_buyer,
    serialize_demand,
    serialize_ice,
    serialize_harbour,
    serialize_landing,
    serialize_price,
    serialize_storage,
    serialize_species,
)
from app.extensions import db
from app.models import (
    Announcement,
    Auction,
    Buyer,
    BuyerDemand,
    ColdStorage,
    FishPrice,
    FishSpecies,
    Harbour,
    HarbourAlert,
    IcePlant,
    Landing,
    utcnow,
)
from app.services.common import get_harbour_or_404, get_species_or_404


def latest_prices(species_id=None, harbour_id=None, limit=100):
    query = FishPrice.query.join(FishPrice.harbour).join(FishPrice.species)
    if species_id is not None:
        query = query.filter(FishPrice.species_id == species_id)
    if harbour_id is not None:
        query = query.filter(FishPrice.harbour_id == harbour_id)
    records = query.order_by(desc(FishPrice.recorded_at), desc(FishPrice.id)).limit(500).all()
    latest = {}
    for record in records:
        latest.setdefault((record.harbour_id, record.species_id), record)
    return [serialize_price(record) for record in list(latest.values())[:limit]]


def list_prices(species_id=None, harbour_id=None, limit=100):
    if species_id is not None:
        get_species_or_404(species_id)
    if harbour_id is not None:
        get_harbour_or_404(harbour_id)
    return latest_prices(species_id, harbour_id, limit)


def list_species():
    return [serialize_species(item) for item in FishSpecies.query.order_by(FishSpecies.name).all()]


def _harbour_buyers(harbour):
    # BuyerDemand has no harbour FK in the current schema; location is the
    # available MVP association until demand is explicitly harbour-scoped.
    token = harbour.name.lower()
    return Buyer.query.filter(
        Buyer.status == "ACTIVE",
        db.func.lower(Buyer.location).contains(token),
    ).order_by(Buyer.id).limit(100).all()


def _harbour_demand(harbour, species_id):
    buyers = _harbour_buyers(harbour)
    buyer_ids = [buyer.id for buyer in buyers]
    if not buyer_ids:
        return {
            "remaining_quantity_kg": 0.0,
            **provenance(None, "UNKNOWN", None),
        }
    query = BuyerDemand.query.filter(
        BuyerDemand.buyer_id.in_(buyer_ids),
        BuyerDemand.species_id == species_id,
        BuyerDemand.status.in_({"OPEN", "PARTIAL"}),
    )
    total, confidence, recorded_at, count = db.session.query(
        db.func.sum(BuyerDemand.requested_quantity_kg - BuyerDemand.fulfilled_quantity_kg),
        db.func.avg(BuyerDemand.confidence),
        db.func.max(BuyerDemand.recorded_at),
        db.func.count(BuyerDemand.id),
    ).filter(
        BuyerDemand.buyer_id.in_(buyer_ids),
        BuyerDemand.species_id == species_id,
        BuyerDemand.status.in_({"OPEN", "PARTIAL"}),
    ).one()
    sources = {
        row[0] for row in query.with_entities(BuyerDemand.source).distinct().limit(10).all()
    }
    source = next(iter(sources)) if len(sources) == 1 else ("MIXED" if sources else "UNKNOWN")
    confidence = round(confidence, 3) if count else None
    result = {
        "remaining_quantity_kg": max(0, total or 0),
        **provenance(recorded_at, source, confidence),
    }
    if "DEMO" in sources:
        result["is_demo"] = True
        result["is_demo_data"] = True
        result["data_label"] = "FICTIONAL PROTOTYPE DATA"
        result["freshness"] = "HISTORICAL"
    return result


def compare_markets(species_id, quantity_kg, current_harbour_id=None):
    species = get_species_or_404(species_id)
    current_harbour = get_harbour_or_404(current_harbour_id) if current_harbour_id else None
    harbours = Harbour.query.filter(Harbour.status != "CLOSED").order_by(Harbour.name).all()
    markets = []
    for harbour in harbours:
        price = FishPrice.query.filter_by(harbour_id=harbour.id, species_id=species.id).order_by(
            FishPrice.recorded_at.desc(), FishPrice.id.desc()
        ).first()
        buyers = _harbour_buyers(harbour)
        ice = IcePlant.query.filter_by(harbour_id=harbour.id).first()
        storage = ColdStorage.query.filter_by(harbour_id=harbour.id).first()
        recent_landing = Landing.query.filter_by(harbour_id=harbour.id, species_id=species.id).order_by(
            Landing.recorded_at.desc(), Landing.id.desc()
        ).first()
        serialized_price = serialize_price(price) if price else None
        demand = _harbour_demand(harbour, species.id)
        freshness_states = [
            serialized_price["freshness"] if serialized_price else "HISTORICAL",
            demand["freshness"],
            provenance(ice.recorded_at, ice.source, ice.confidence)["freshness"] if ice else "HISTORICAL",
            provenance(storage.recorded_at, storage.source, storage.confidence)["freshness"] if storage else "HISTORICAL",
        ]
        aggregate_freshness = (
            "HISTORICAL" if "HISTORICAL" in freshness_states
            else "RECENT" if "RECENT" in freshness_states
            else "LIVE"
        )
        markets.append({
            "harbour": serialize_harbour(harbour),
            "is_current_harbour": current_harbour is not None and harbour.id == current_harbour.id,
            "price": serialized_price,
            "demand": demand,
            "active_buyers": len(buyers),
            "supply": serialize_landing(recent_landing) if recent_landing else None,
            "ice_available": ice.available_tonnes if ice and ice.status != "CLOSED" else (0 if ice else None),
            "ice_status": ice.status if ice else None,
            "ice": provenance(ice.recorded_at, ice.source, ice.confidence) if ice else None,
            "storage_available": storage.available_tonnes if storage and storage.status != "CLOSED" else (0 if storage else None),
            "storage_status": storage.status if storage else None,
            "storage": provenance(storage.recorded_at, storage.source, storage.confidence) if storage else None,
            "freshness": aggregate_freshness,
            "is_demo": bool(
                (serialized_price and serialized_price["is_demo"])
                or demand["is_demo"]
                or (ice and ice.source == "DEMO")
                or (storage and storage.source == "DEMO")
                or (recent_landing and recent_landing.source == "DEMO")
            ),
            "is_demo_data": bool(
                (serialized_price and serialized_price["is_demo_data"])
                or demand["is_demo_data"]
                or (ice and ice.source == "DEMO")
                or (storage and storage.source == "DEMO")
                or (recent_landing and recent_landing.source == "DEMO")
            ),
        })
    return {
        "species": serialize_species(species),
        "quantity_kg": quantity_kg,
        "current_harbour": serialize_harbour(current_harbour) if current_harbour else None,
        "demand_attribution": (
            "Buyer demand is associated with a harbour by matching buyer.location; "
            "BuyerDemand is not harbour-scoped in the current schema."
        ),
        "is_demo": any(market["is_demo_data"] for market in markets),
        "markets": markets,
    }


def harbour_dashboard(harbour_id):
    harbour = get_harbour_or_404(harbour_id)
    landings = Landing.query.filter_by(harbour_id=harbour.id).order_by(
        Landing.landing_time.desc(), Landing.id.desc()
    ).limit(10).all()
    all_prices = FishPrice.query.filter_by(harbour_id=harbour.id).order_by(
        FishPrice.recorded_at.desc(), FishPrice.id.desc()
    ).limit(100).all()
    latest_by_species = {}
    for price in all_prices:
        latest_by_species.setdefault(price.species_id, price)
    auctions = Auction.query.filter_by(harbour_id=harbour.id).filter(
        Auction.status.in_({"SCHEDULED", "LIVE"})
    ).order_by(Auction.created_at.desc()).limit(10).all()
    buyers = _harbour_buyers(harbour)
    demands = BuyerDemand.query.filter(
        BuyerDemand.buyer_id.in_([buyer.id for buyer in buyers] or [-1]),
        BuyerDemand.status.in_({"OPEN", "PARTIAL"}),
    ).order_by(BuyerDemand.updated_at.desc()).limit(20).all()
    ice = IcePlant.query.filter_by(harbour_id=harbour.id).first()
    storage = ColdStorage.query.filter_by(harbour_id=harbour.id).first()
    announcements = Announcement.query.filter(
        db.or_(Announcement.harbour_id == harbour.id, Announcement.harbour_id.is_(None))
    ).filter(
        db.or_(Announcement.expires_at.is_(None), Announcement.expires_at > utcnow())
    ).order_by(Announcement.published_at.desc()).limit(10).all()
    alerts = HarbourAlert.query.filter_by(harbour_id=harbour.id, active=True).filter(
        db.or_(HarbourAlert.expires_at.is_(None), HarbourAlert.expires_at > utcnow())
    ).order_by(
        HarbourAlert.created_at.desc()
    ).limit(10).all()
    return {
        "harbour": serialize_harbour(harbour),
        "recent_landings": [serialize_landing(item) for item in landings],
        "prices": [serialize_price(item) for item in latest_by_species.values()],
        "active_auctions": [serialize_auction(item) for item in auctions],
        "active_buyers": [serialize_buyer(item) for item in buyers[:20]],
        "buyer_demand": [serialize_demand(item) for item in demands],
        "demand_attribution": "Buyer location matched against harbour name; demand is not directly harbour-scoped.",
        "ice": serialize_ice(ice),
        "cold_storage": serialize_storage(storage),
        "announcements": [serialize_announcement(item) for item in announcements],
        "active_alerts": [serialize_alert(item) for item in alerts],
    }


def harbour_changes(harbour_id, limit=25):
    harbour = get_harbour_or_404(harbour_id)
    events = []
    for item in Landing.query.filter_by(harbour_id=harbour.id).order_by(
        Landing.recorded_at.desc(), Landing.id.desc()
    ).limit(limit).all():
        events.append({
            "kind": "observed_event",
            "type": "LANDING_RECORDED",
            "observed_at": item.recorded_at.isoformat() + "Z",
            "summary": f"{item.quantity_kg:g} kg {item.species.name} landing recorded.",
            **provenance(item.recorded_at, item.source, item.confidence),
            "trend": None,
        })
    for item in Auction.query.filter_by(harbour_id=harbour.id).order_by(
        Auction.created_at.desc(), Auction.id.desc()
    ).limit(limit).all():
        events.append({
            "kind": "observed_event",
            "type": "AUCTION_RECORDED",
            "observed_at": item.created_at.isoformat() + "Z",
            "summary": f"{item.species.name} auction is {item.status.lower()} for {item.quantity_kg:g} kg.",
            **provenance(item.recorded_at or item.created_at, item.source, item.confidence),
            "trend": None,
        })
    for item in FishPrice.query.filter_by(harbour_id=harbour.id).order_by(
        FishPrice.recorded_at.desc(), FishPrice.id.desc()
    ).limit(10).all():
        events.append({
            "kind": "observed_snapshot",
            "type": "PRICE_OBSERVED",
            "observed_at": item.recorded_at.isoformat() + "Z",
            "summary": f"Recorded indicative {item.species.name} average price: ₹{item.average_price:g}/kg.",
            **provenance(item.recorded_at, item.source, item.confidence),
            "trend": None,
        })
    ice = IcePlant.query.filter_by(harbour_id=harbour.id).first()
    if ice:
        events.append({
            "kind": "observed_snapshot",
            "type": "ICE_AVAILABILITY_OBSERVED",
            "observed_at": ice.recorded_at.isoformat() + "Z",
            "summary": f"Ice availability recorded at {ice.available_tonnes:g} tonnes.",
            **provenance(ice.recorded_at, ice.source, ice.confidence),
            "trend": None,
        })
    storage = ColdStorage.query.filter_by(harbour_id=harbour.id).first()
    if storage:
        events.append({
            "kind": "observed_snapshot",
            "type": "STORAGE_AVAILABILITY_OBSERVED",
            "observed_at": storage.recorded_at.isoformat() + "Z",
            "summary": f"Derived cold storage availability is {storage.available_tonnes:g} tonnes.",
            **provenance(storage.recorded_at, storage.source, storage.confidence),
            "trend": None,
        })
    for item in HarbourAlert.query.filter_by(harbour_id=harbour.id).order_by(
        HarbourAlert.created_at.desc(), HarbourAlert.id.desc()
    ).limit(limit).all():
        events.append({
            "kind": "observed_event",
            "type": "ALERT_RECORDED",
            "observed_at": item.created_at.isoformat() + "Z",
            "summary": item.title,
            "source": item.source,
            "is_demo": item.source == "DEMO",
            "is_demo_data": item.source == "DEMO",
            "trend": None,
        })
    events.sort(key=lambda item: item["observed_at"], reverse=True)
    return {
        "harbour": serialize_harbour(harbour),
        "events": events[:limit],
        "note": "Events are observations. Historical values are insufficient to calculate price or resource trends.",
    }
