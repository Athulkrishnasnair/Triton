"""Insert or refresh a repeatable Harbour OS prototype dataset.

Run from backend/: python seed.py
All seeded records are fictional and carry source=DEMO where provenance applies.
"""

from datetime import datetime
import os

from app import create_app
from app.extensions import db
from app.models import (
    Announcement,
    Auction,
    AuctionBid,
    Buyer,
    BuyerDemand,
    ColdStorage,
    FishPrice,
    FishSpecies,
    Harbour,
    HarbourAlert,
    IcePlant,
    Landing,
)


DEMO_AS_OF = datetime(2026, 10, 7, 10, 42)

HARBOURS = [
    {"name": "Munambam", "district": "Ernakulam", "latitude": 10.1707, "longitude": 76.1650},
    {"name": "Kochi", "district": "Ernakulam", "latitude": 9.9312, "longitude": 76.2673},
    {"name": "Beypore", "district": "Kozhikode", "latitude": 11.1760, "longitude": 75.8060},
]

SPECIES = [
    {"name": "Sardine", "local_name": "Mathi (മത്തി)", "scientific_name": "Sardinella longiceps"},
    {"name": "Mackerel", "local_name": "Ayala (അയല)", "scientific_name": "Rastrelliger kanagurta"},
    {"name": "Anchovy", "local_name": "Netholi (നെത്തോലി)", "scientific_name": "Stolephorus indicus"},
    {"name": "Tuna", "local_name": "Choora (ചൂര)", "scientific_name": "Thunnus albacares"},
    {"name": "Pomfret", "local_name": "Avoli (ആവോലി)", "scientific_name": "Pampus argenteus"},
    {"name": "Prawn / Shrimp", "local_name": "Chemmeen (ചെമ്മീൻ)", "scientific_name": None},
]

BUYERS = [
    {"key": "munambam_fresh", "name": "Munambam Fresh Catch", "organization": "Demo buyer cooperative", "location": "Munambam, Ernakulam"},
    {"key": "coastal_select", "name": "Coastal Select", "organization": "Demo seafood wholesaler", "location": "Munambam, Ernakulam"},
    {"key": "kochi_market", "name": "Kochi Market Foods", "organization": "Demo wholesale buyer", "location": "Kochi, Ernakulam"},
    {"key": "harbour_catch", "name": "Harbour Catch Traders", "organization": "Demo seafood trader", "location": "Kochi, Ernakulam"},
    {"key": "kochi_food_services", "name": "Kochi Food Services", "organization": "Demo food service buyer", "location": "Kochi, Ernakulam"},
    {"key": "beypore_fisheries", "name": "Beypore Fisheries Buyer Group", "organization": "Demo buyer group", "location": "Beypore, Kozhikode"},
    {"key": "north_coast", "name": "North Coast Seafood", "organization": "Demo seafood wholesaler", "location": "Beypore, Kozhikode"},
]

# Harbour-specific sardine observations intentionally vary to support the
# later comparison story. These are fictional prototype values, not live quotes.
HARBOUR_MARKET = {
    "Munambam": {
        "price": (155, 176, 168, 4200),
        "landing_kg": 6800,
        "demand": (3200, 1800),
        "ice": (42, 18, 3.5, 12),
        "storage": (80, 57, 8),
        "auction": (500, 162, 174),
    },
    "Kochi": {
        "price": (169, 190, 181, 2700),
        "landing_kg": 2900,
        "demand": (5200, 3100, 1900),
        "ice": (70, 46, 3.8, 5),
        "storage": (120, 94, 14),
        "auction": (700, 175, 188),
    },
    "Beypore": {
        "price": (148, 172, 160, 3500),
        "landing_kg": 5100,
        "demand": (2100, 1200),
        "ice": (55, 34, 3.2, 7),
        "storage": (95, 66, 10),
        "auction": (600, 155, 169),
    },
}


def reset_harbour_data():
    """Reset operational demo tables in dependency order, retaining auth users."""
    if os.environ.get("APP_ENV", "development").casefold() in {"production", "prod"}:
        raise RuntimeError("Refusing to reset Harbour OS data when APP_ENV is production.")
    for model in (
        AuctionBid,
        BuyerDemand,
        Auction,
        FishPrice,
        Landing,
        IcePlant,
        ColdStorage,
        HarbourAlert,
        Announcement,
        Buyer,
        FishSpecies,
        Harbour,
    ):
        db.session.query(model).delete(synchronize_session=False)
    db.session.commit()


def ensure(model, lookup, values):
    """Create or refresh one row using a stable natural-key lookup."""
    row = model.query.filter_by(**lookup).order_by(model.id.asc()).first()
    if row is None:
        row = model(**lookup)
        db.session.add(row)
    for field, value in values.items():
        setattr(row, field, value)
    return row


def seed():
    app = create_app()
    with app.app_context():
        try:
            reset_harbour_data()
            harbours = {
                item["name"]: ensure(Harbour, {"name": item["name"]}, item)
                for item in HARBOURS
            }
            species = {
                item["name"]: ensure(FishSpecies, {"name": item["name"]}, item)
                for item in SPECIES
            }
            buyers = {
                item["key"]: ensure(
                    Buyer,
                    {"name": item["name"]},
                    {
                        "organization": item["organization"],
                        "location": item["location"],
                        "status": "ACTIVE",
                    },
                )
                for item in BUYERS
            }
            db.session.flush()

            landings = []
            prices = []
            demands = []
            auctions = []
            bids = []
            for harbour_name, data in HARBOUR_MARKET.items():
                harbour = harbours[harbour_name]
                sardine = species["Sardine"]
                landing_time = DEMO_AS_OF.replace(hour=8, minute=15)
                landing = ensure(
                    Landing,
                    {"harbour_id": harbour.id, "species_id": sardine.id, "landing_time": landing_time},
                    {
                        "quantity_kg": data["landing_kg"],
                        "quality_grade": "A",
                        "recorded_at": DEMO_AS_OF,
                        "source": "DEMO",
                        "confidence": 0.9,
                    },
                )
                landings.append(landing)

                minimum, maximum, average, market_quantity = data["price"]
                price = ensure(
                    FishPrice,
                    {"harbour_id": harbour.id, "species_id": sardine.id, "recorded_at": DEMO_AS_OF},
                    {
                        "min_price": minimum,
                        "max_price": maximum,
                        "average_price": average,
                        "quantity_kg": market_quantity,
                        "source": "DEMO",
                        "confidence": 0.75,
                    },
                )
                prices.append(price)

                buyer_keys = {
                    "Munambam": ("munambam_fresh", "coastal_select"),
                    "Kochi": ("kochi_market", "harbour_catch", "kochi_food_services"),
                    "Beypore": ("beypore_fisheries", "north_coast"),
                }[harbour_name]
                for index, buyer_key in enumerate(buyer_keys):
                    buyer = buyers[buyer_key]
                    demand = ensure(
                        BuyerDemand,
                        {"buyer_id": buyer.id, "species_id": sardine.id},
                        {
                            "requested_quantity_kg": data["demand"][index],
                            "fulfilled_quantity_kg": (400 if index == 0 else 250),
                            "priority": "HIGH" if index == 0 else "NORMAL",
                            "status": "PARTIAL",
                            "recorded_at": DEMO_AS_OF,
                            "confidence": 0.85,
                            "updated_at": DEMO_AS_OF,
                        },
                    )
                    demands.append(demand)

                capacity, available, price_per_kg, queue = data["ice"]
                ensure(
                    IcePlant,
                    {"harbour_id": harbour.id},
                    {
                        "capacity_tonnes": capacity,
                        "available_tonnes": available,
                        "price_per_kg": price_per_kg,
                        "queue_count": queue,
                        "status": "AVAILABLE",
                        "source": "DEMO",
                        "recorded_at": DEMO_AS_OF,
                        "confidence": 0.85,
                        "updated_at": DEMO_AS_OF,
                    },
                )

                capacity, occupied, reserved = data["storage"]
                ensure(
                    ColdStorage,
                    {"harbour_id": harbour.id},
                    {
                        "capacity_tonnes": capacity,
                        "occupied_tonnes": occupied,
                        "reserved_tonnes": reserved,
                        "expected_release": DEMO_AS_OF.replace(hour=16),
                        "status": "AVAILABLE",
                        "source": "DEMO",
                        "recorded_at": DEMO_AS_OF,
                        "confidence": 0.8,
                        "updated_at": DEMO_AS_OF,
                    },
                )

                quantity, start_price, current_price = data["auction"]
                auction = ensure(
                    Auction,
                    {"harbour_id": harbour.id, "species_id": sardine.id, "created_at": DEMO_AS_OF},
                    {
                        "quantity_kg": quantity,
                        "quality_grade": "A",
                        "starting_price": start_price,
                        "current_price": current_price,
                        "status": "LIVE",
                        "source": "DEMO",
                        "confidence": 0.8,
                        "recorded_at": DEMO_AS_OF,
                        "started_at": DEMO_AS_OF.replace(hour=10, minute=15),
                    },
                )
                auctions.append(auction)
                db.session.flush()
                # Replaying the seed restores the fixture auction's known bid
                # state after an interactive demo, without touching other lots.
                AuctionBid.query.filter_by(auction_id=auction.id).delete(synchronize_session=False)
                for index, buyer_key in enumerate(buyer_keys):
                    bid_time = DEMO_AS_OF.replace(minute=20 + index)
                    bid = ensure(
                        AuctionBid,
                        {"auction_id": auction.id, "buyer_id": buyers[buyer_key].id, "timestamp": bid_time},
                        {"amount": current_price - (2 if index == 0 else 0)},
                    )
                    bids.append(bid)

            # Extra landing and price coverage gives each harbour a broader market sample.
            for harbour_name, species_name, quantity, price in [
                ("Munambam", "Mackerel", 1900, 228),
                ("Kochi", "Anchovy", 1200, 194),
                ("Beypore", "Mackerel", 1600, 221),
            ]:
                harbour = harbours[harbour_name]
                fish = species[species_name]
                landing_time = DEMO_AS_OF.replace(hour=8, minute=35)
                landing = ensure(
                    Landing,
                    {"harbour_id": harbour.id, "species_id": fish.id, "landing_time": landing_time},
                    {
                        "quantity_kg": quantity,
                        "quality_grade": "B",
                        "recorded_at": DEMO_AS_OF,
                        "source": "DEMO",
                        "confidence": 0.85,
                    },
                )
                landings.append(landing)
                market_price = ensure(
                    FishPrice,
                    {"harbour_id": harbour.id, "species_id": fish.id, "recorded_at": DEMO_AS_OF},
                    {
                        "min_price": price - 15,
                        "max_price": price + 12,
                        "average_price": price,
                        "quantity_kg": quantity,
                        "source": "DEMO",
                        "confidence": 0.7,
                    },
                )
                prices.append(market_price)

            announcement_specs = [
                ("Munambam", "Prototype auction schedule", "DEMO NOTICE: Sardine auction window shown for the prototype is 10:15–11:30.", "NORMAL"),
                ("Kochi", "Prototype buyer demand update", "DEMO NOTICE: Buyer demand figures are sample entries for demonstration.", "NORMAL"),
                ("Beypore", "Prototype harbour operations", "DEMO NOTICE: Harbour resource availability is sample data.", "LOW"),
                (None, "Harbour OS prototype data", "All prices, demand, landing, and resource figures in this demonstration are fictional.", "HIGH"),
            ]
            announcements = []
            for harbour_name, title, message, priority in announcement_specs:
                harbour_id = harbours[harbour_name].id if harbour_name else None
                announcement = ensure(
                    Announcement,
                    {"harbour_id": harbour_id, "title": title},
                    {
                        "message": message,
                        "priority": priority,
                        "published_at": DEMO_AS_OF,
                        "expires_at": DEMO_AS_OF.replace(day=8),
                        "source": "DEMO",
                    },
                )
                announcements.append(announcement)

            alert_specs = [
                ("Munambam", "ICE_SHORTAGE", "Demo ice queue", "Sample queue pressure indicator; verify with the harbour operator.", "WARNING"),
                ("Kochi", "STORAGE_LIMIT", "Demo cold-storage pressure", "Sample storage availability; figures are not live capacity.", "INFO"),
                ("Beypore", "HIGH_LANDING_VOLUME", "Demo landing volume", "Sample landing level for prototype comparison.", "INFO"),
            ]
            alerts = []
            for harbour_name, alert_type, title, message, severity in alert_specs:
                alert = ensure(
                    HarbourAlert,
                    {"harbour_id": harbours[harbour_name].id, "type": alert_type, "title": title},
                    {
                        "message": message,
                        "severity": severity,
                        "active": True,
                        "created_at": DEMO_AS_OF,
                        "expires_at": DEMO_AS_OF.replace(day=8),
                        "source": "DEMO",
                    },
                )
                alerts.append(alert)

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        print("Harbour OS demo data reset and seeded (all figures are fictional; source=DEMO).")
        for model, label in [
            (Harbour, "harbours"),
            (FishSpecies, "species"),
            (Landing, "landings"),
            (FishPrice, "fish prices"),
            (Buyer, "buyers"),
            (BuyerDemand, "buyer demands"),
            (Auction, "auctions"),
            (AuctionBid, "auction bids"),
            (IcePlant, "ice plants"),
            (ColdStorage, "cold storages"),
            (Announcement, "announcements"),
            (HarbourAlert, "alerts"),
        ]:
            print(f"{label}: {model.query.count()}")


if __name__ == "__main__":
    seed()
