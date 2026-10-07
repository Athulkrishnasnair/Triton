"""SQLAlchemy models for Harbour OS and the preserved authentication system."""

from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow():
    """Return a naive UTC timestamp, matching SQLite's existing datetime use."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    """Authentication identity; kept compatible with the existing auth routes."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    buyer_profile = db.relationship("Buyer", back_populates="user", uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Harbour(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    district = db.Column(db.String(120), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    landings = db.relationship("Landing", back_populates="harbour")
    fish_prices = db.relationship("FishPrice", back_populates="harbour")
    auctions = db.relationship("Auction", back_populates="harbour")
    ice_plants = db.relationship("IcePlant", back_populates="harbour")
    cold_storages = db.relationship("ColdStorage", back_populates="harbour")
    announcements = db.relationship("Announcement", back_populates="harbour")
    alerts = db.relationship("HarbourAlert", back_populates="harbour")


class FishSpecies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    local_name = db.Column(db.String(120), nullable=False)
    scientific_name = db.Column(db.String(160))
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    landings = db.relationship("Landing", back_populates="species")
    fish_prices = db.relationship("FishPrice", back_populates="species")
    buyer_demands = db.relationship("BuyerDemand", back_populates="species")
    auctions = db.relationship("Auction", back_populates="species")


class Landing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    harbour_id = db.Column(db.Integer, db.ForeignKey("harbour.id"), nullable=False, index=True)
    species_id = db.Column(db.Integer, db.ForeignKey("fish_species.id"), nullable=False, index=True)
    quantity_kg = db.Column(db.Float, nullable=False)
    quality_grade = db.Column(db.String(1))
    landing_time = db.Column(db.DateTime, nullable=False, index=True)
    recorded_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    source = db.Column(db.String(40), nullable=False, default="DEMO", index=True)
    confidence = db.Column(db.Float, nullable=False, default=1.0)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    harbour = db.relationship("Harbour", back_populates="landings")
    species = db.relationship("FishSpecies", back_populates="landings")


class FishPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    harbour_id = db.Column(db.Integer, db.ForeignKey("harbour.id"), nullable=False, index=True)
    species_id = db.Column(db.Integer, db.ForeignKey("fish_species.id"), nullable=False, index=True)
    min_price = db.Column(db.Float, nullable=False)
    max_price = db.Column(db.Float, nullable=False)
    average_price = db.Column(db.Float, nullable=False)
    quantity_kg = db.Column(db.Float)
    recorded_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    source = db.Column(db.String(40), nullable=False, default="DEMO", index=True)
    confidence = db.Column(db.Float, nullable=False, default=1.0)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    harbour = db.relationship("Harbour", back_populates="fish_prices")
    species = db.relationship("FishSpecies", back_populates="fish_prices")


class Buyer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    organization = db.Column(db.String(160))
    location = db.Column(db.String(160))
    contact = db.Column(db.String(80))
    status = db.Column(db.String(20), nullable=False, default="ACTIVE", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    user = db.relationship("User", back_populates="buyer_profile")
    demands = db.relationship("BuyerDemand", back_populates="buyer")
    bids = db.relationship("AuctionBid", back_populates="buyer")


class BuyerDemand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("buyer.id"), nullable=False, index=True)
    species_id = db.Column(db.Integer, db.ForeignKey("fish_species.id"), nullable=False, index=True)
    requested_quantity_kg = db.Column(db.Float, nullable=False)
    fulfilled_quantity_kg = db.Column(db.Float, nullable=False, default=0)
    priority = db.Column(db.String(20), nullable=False, default="NORMAL")
    status = db.Column(db.String(20), nullable=False, default="OPEN", index=True)
    source = db.Column(db.String(40), nullable=False, default="DEMO", index=True)
    recorded_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    confidence = db.Column(db.Float, nullable=False, default=1.0)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    buyer = db.relationship("Buyer", back_populates="demands")
    species = db.relationship("FishSpecies", back_populates="buyer_demands")

    @property
    def remaining_quantity_kg(self):
        return max(0, self.requested_quantity_kg - self.fulfilled_quantity_kg)


class Auction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    harbour_id = db.Column(db.Integer, db.ForeignKey("harbour.id"), nullable=False, index=True)
    species_id = db.Column(db.Integer, db.ForeignKey("fish_species.id"), nullable=False, index=True)
    quantity_kg = db.Column(db.Float, nullable=False)
    quality_grade = db.Column(db.String(1))
    starting_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="SCHEDULED", index=True)
    started_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)
    winner_id = db.Column(db.Integer, db.ForeignKey("buyer.id"), index=True)
    source = db.Column(db.String(40), nullable=False, default="DEMO", index=True)
    confidence = db.Column(db.Float, nullable=False, default=1.0)
    recorded_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    harbour = db.relationship("Harbour", back_populates="auctions")
    species = db.relationship("FishSpecies", back_populates="auctions")
    winner = db.relationship("Buyer", foreign_keys=[winner_id])
    bids = db.relationship("AuctionBid", back_populates="auction")


class AuctionBid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auction_id = db.Column(db.Integer, db.ForeignKey("auction.id"), nullable=False, index=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("buyer.id"), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    auction = db.relationship("Auction", back_populates="bids")
    buyer = db.relationship("Buyer", back_populates="bids")


class IcePlant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    harbour_id = db.Column(db.Integer, db.ForeignKey("harbour.id"), nullable=False, unique=True, index=True)
    capacity_tonnes = db.Column(db.Float, nullable=False)
    available_tonnes = db.Column(db.Float, nullable=False)
    price_per_kg = db.Column(db.Float, nullable=False)
    queue_count = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="AVAILABLE", index=True)
    source = db.Column(db.String(40), nullable=False, default="DEMO", index=True)
    recorded_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    confidence = db.Column(db.Float, nullable=False, default=1.0)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    harbour = db.relationship("Harbour", back_populates="ice_plants")


class ColdStorage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    harbour_id = db.Column(db.Integer, db.ForeignKey("harbour.id"), nullable=False, unique=True, index=True)
    capacity_tonnes = db.Column(db.Float, nullable=False)
    occupied_tonnes = db.Column(db.Float, nullable=False, default=0)
    reserved_tonnes = db.Column(db.Float, nullable=False, default=0)
    expected_release = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False, default="AVAILABLE", index=True)
    source = db.Column(db.String(40), nullable=False, default="DEMO", index=True)
    recorded_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    confidence = db.Column(db.Float, nullable=False, default=1.0)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    harbour = db.relationship("Harbour", back_populates="cold_storages")

    @property
    def available_tonnes(self):
        return max(0, self.capacity_tonnes - self.occupied_tonnes - self.reserved_tonnes)


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    harbour_id = db.Column(db.Integer, db.ForeignKey("harbour.id"), index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="NORMAL", index=True)
    published_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    expires_at = db.Column(db.DateTime)
    source = db.Column(db.String(40), nullable=False, default="DEMO", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    harbour = db.relationship("Harbour", back_populates="announcements")


class HarbourAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    harbour_id = db.Column(db.Integer, db.ForeignKey("harbour.id"), nullable=False, index=True)
    type = db.Column(db.String(40), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False, default="INFO", index=True)
    active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    source = db.Column(db.String(40), nullable=False, default="DEMO", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    expires_at = db.Column(db.DateTime)

    harbour = db.relationship("Harbour", back_populates="alerts")
