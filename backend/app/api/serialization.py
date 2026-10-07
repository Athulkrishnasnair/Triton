from datetime import datetime, timezone

from app.models import AuctionBid


def isoformat(value):
    if value is None:
        return None
    # Database datetimes are naive UTC values under the existing SQLite setup.
    return value.isoformat(timespec="seconds") + ("Z" if value.tzinfo is None else "")


def freshness(recorded_at, source=None, now=None):
    is_demo = (source or "").upper() == "DEMO"
    if is_demo or recorded_at is None:
        # Prototype timestamps do not represent a live feed, even when recent.
        return "HISTORICAL"
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    age_seconds = max(0, (now - recorded_at.replace(tzinfo=None)).total_seconds())
    if age_seconds <= 5 * 60:
        return "LIVE"
    if age_seconds <= 60 * 60:
        return "RECENT"
    return "HISTORICAL"


def provenance(recorded_at, source, confidence):
    is_demo = (source or "").upper() == "DEMO"
    result = {
        "source": source,
        "confidence": confidence,
        "recorded_at": isoformat(recorded_at),
        "freshness": freshness(recorded_at, source),
        "is_demo": is_demo,
        "is_demo_data": is_demo,
    }
    if is_demo:
        result["data_label"] = "FICTIONAL PROTOTYPE DATA"
    return result


def serialize_harbour(harbour):
    return {
        "id": harbour.id,
        "name": harbour.name,
        "district": harbour.district,
        "latitude": harbour.latitude,
        "longitude": harbour.longitude,
        "status": harbour.status,
        "created_at": isoformat(harbour.created_at),
        "updated_at": isoformat(harbour.updated_at),
    }


def serialize_species(species):
    return {
        "id": species.id,
        "name": species.name,
        "local_name": species.local_name,
        "scientific_name": species.scientific_name,
    }


def serialize_landing(landing):
    return {
        "id": landing.id,
        "harbour_id": landing.harbour_id,
        "harbour": landing.harbour.name,
        "species_id": landing.species_id,
        "species": landing.species.name,
        "quantity_kg": landing.quantity_kg,
        "quality_grade": landing.quality_grade,
        "landing_time": isoformat(landing.landing_time),
        **provenance(landing.recorded_at, landing.source, landing.confidence),
    }


def serialize_price(price):
    return {
        "id": price.id,
        "harbour_id": price.harbour_id,
        "harbour": price.harbour.name,
        "species_id": price.species_id,
        "species": price.species.name,
        "value": price.average_price,
        "min_price": price.min_price,
        "max_price": price.max_price,
        "average_price": price.average_price,
        "quantity_kg": price.quantity_kg,
        **provenance(price.recorded_at, price.source, price.confidence),
    }


def serialize_demand(demand):
    return {
        "id": demand.id,
        "buyer_id": demand.buyer_id,
        "buyer": demand.buyer.name,
        "species_id": demand.species_id,
        "species": demand.species.name,
        "requested_quantity_kg": demand.requested_quantity_kg,
        "fulfilled_quantity_kg": demand.fulfilled_quantity_kg,
        "remaining_quantity_kg": demand.remaining_quantity_kg,
        "priority": demand.priority,
        "status": demand.status,
        **provenance(demand.recorded_at, demand.source, demand.confidence),
    }


def serialize_buyer(buyer):
    is_demo = (buyer.organization or "").casefold().startswith("demo ")
    return {
        "id": buyer.id,
        "name": buyer.name,
        "organization": buyer.organization,
        "location": buyer.location,
        "status": buyer.status,
        "created_at": isoformat(buyer.created_at),
        "updated_at": isoformat(buyer.updated_at),
        "source": "DEMO" if is_demo else "UNKNOWN",
        "is_demo": is_demo,
        "is_demo_data": is_demo,
        **({"data_label": "FICTIONAL PROTOTYPE BUYER"} if is_demo else {}),
    }


def serialize_auction(auction, include_bids=False):
    result = {
        "id": auction.id,
        "harbour_id": auction.harbour_id,
        "harbour": auction.harbour.name,
        "species_id": auction.species_id,
        "species": auction.species.name,
        "quantity_kg": auction.quantity_kg,
        "quality_grade": auction.quality_grade,
        "starting_price": auction.starting_price,
        "current_price": auction.current_price,
        "status": auction.status,
        "started_at": isoformat(auction.started_at),
        "closed_at": isoformat(auction.closed_at),
        "winner": serialize_buyer(auction.winner) if auction.winner else None,
        "created_at": isoformat(auction.created_at),
        **provenance(auction.recorded_at or auction.created_at, auction.source, auction.confidence),
    }
    if include_bids:
        bids = AuctionBid.query.filter_by(auction_id=auction.id).order_by(
            AuctionBid.timestamp.desc(), AuctionBid.id.desc()
        ).limit(20).all()
        result["bids"] = [
            {
                "id": bid.id,
                "buyer": serialize_buyer(bid.buyer),
                "amount": bid.amount,
                "timestamp": isoformat(bid.timestamp),
                **provenance(bid.timestamp, auction.source, auction.confidence),
            }
            for bid in bids
        ]
    return result


def serialize_announcement(announcement):
    return {
        "id": announcement.id,
        "harbour_id": announcement.harbour_id,
        "harbour": announcement.harbour.name if announcement.harbour else None,
        "title": announcement.title,
        "message": announcement.message,
        "priority": announcement.priority,
        "published_at": isoformat(announcement.published_at),
        "expires_at": isoformat(announcement.expires_at),
        "source": announcement.source,
        "is_demo": announcement.source == "DEMO",
        "is_demo_data": announcement.source == "DEMO",
        **({"data_label": "FICTIONAL PROTOTYPE DATA"} if announcement.source == "DEMO" else {}),
    }


def serialize_alert(alert):
    return {
        "id": alert.id,
        "harbour_id": alert.harbour_id,
        "harbour": alert.harbour.name,
        "type": alert.type,
        "title": alert.title,
        "message": alert.message,
        "severity": alert.severity,
        "active": alert.active,
        "created_at": isoformat(alert.created_at),
        "expires_at": isoformat(alert.expires_at),
        "source": alert.source,
        "is_demo": alert.source == "DEMO",
        "is_demo_data": alert.source == "DEMO",
        **({"data_label": "FICTIONAL PROTOTYPE DATA"} if alert.source == "DEMO" else {}),
    }


def serialize_ice(ice):
    if ice is None:
        return None
    return {
        "id": ice.id,
        "capacity_tonnes": ice.capacity_tonnes,
        "available_tonnes": ice.available_tonnes,
        "price_per_kg": ice.price_per_kg,
        "queue_count": ice.queue_count,
        "status": ice.status,
        **provenance(ice.recorded_at, ice.source, ice.confidence),
    }


def serialize_storage(storage):
    if storage is None:
        return None
    return {
        "id": storage.id,
        "capacity_tonnes": storage.capacity_tonnes,
        "occupied_tonnes": storage.occupied_tonnes,
        "reserved_tonnes": storage.reserved_tonnes,
        "available_tonnes": storage.available_tonnes,
        "expected_release": isoformat(storage.expected_release),
        "status": storage.status,
        **provenance(storage.recorded_at, storage.source, storage.confidence),
    }
