import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

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


class HarbourAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-only-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "CORS_ORIGINS": ["http://localhost:5173"],
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            self.munambam = Harbour(name="Munambam", district="Ernakulam", status="ACTIVE")
            self.kochi = Harbour(name="Kochi", district="Ernakulam", status="ACTIVE")
            self.beypore = Harbour(name="Beypore", district="Kozhikode", status="ACTIVE")
            self.sardine = FishSpecies(name="Sardine", local_name="Mathi")
            self.mackerel = FishSpecies(name="Mackerel", local_name="Ayala")
            db.session.add_all([
                self.munambam, self.kochi, self.beypore, self.sardine, self.mackerel,
            ])
            db.session.flush()
            buyers = [
                Buyer(name="Munambam buyer", location="Munambam, Kerala", status="ACTIVE"),
                Buyer(name="Kochi buyer one", location="Kochi, Kerala", status="ACTIVE"),
                Buyer(name="Kochi buyer two", location="Kochi, Kerala", status="ACTIVE"),
                Buyer(name="Beypore buyer", location="Beypore, Kerala", status="ACTIVE"),
            ]
            db.session.add_all(buyers)
            db.session.flush()
            for harbour, price, demand, ice_tonnes, storage_tonnes, buyer_rows in [
                (self.munambam, 168, 2500, 20, 50, buyers[:1]),
                (self.kochi, 181, 6000, 46, 12, buyers[1:3]),
                (self.beypore, 160, 1500, 30, 30, buyers[3:]),
            ]:
                db.session.add(FishPrice(
                    harbour=harbour, species=self.sardine, min_price=price - 10,
                    max_price=price + 10, average_price=price, recorded_at=now,
                    source="DEMO", confidence=0.8,
                ))
                db.session.add(Landing(
                    harbour=harbour, species=self.sardine, quantity_kg=2200,
                    quality_grade="A", landing_time=now, recorded_at=now,
                    source="DEMO", confidence=0.8,
                ))
                db.session.add(IcePlant(
                    harbour=harbour, capacity_tonnes=60, available_tonnes=ice_tonnes,
                    price_per_kg=3.5, queue_count=4, source="DEMO",
                    recorded_at=now, confidence=0.8,
                ))
                db.session.add(ColdStorage(
                    harbour=harbour, capacity_tonnes=100, occupied_tonnes=storage_tonnes,
                    reserved_tonnes=0, source="DEMO", recorded_at=now, confidence=0.8,
                ))
                for index, buyer in enumerate(buyer_rows):
                    db.session.add(BuyerDemand(
                        buyer=buyer, species=self.sardine,
                        requested_quantity_kg=demand / len(buyer_rows),
                        fulfilled_quantity_kg=0, status="OPEN", source="DEMO",
                        recorded_at=now, confidence=0.8,
                    ))
            auction = Auction(
                harbour=self.kochi, species=self.sardine, quantity_kg=500,
                quality_grade="A", starting_price=170, current_price=181,
                status="LIVE", started_at=now,
            )
            db.session.add(auction)
            db.session.flush()
            db.session.add(AuctionBid(auction=auction, buyer=buyers[1], amount=181, timestamp=now))
            db.session.add(Announcement(
                harbour=self.kochi, title="Demo announcement",
                message="Prototype data.", priority="NORMAL", published_at=now,
            ))
            db.session.add(HarbourAlert(
                harbour=self.kochi, type="MARKET_CHANGE", title="Demo alert",
                message="Prototype data.", severity="INFO", active=True, created_at=now,
            ))
            db.session.commit()
            self.species_id = self.sardine.id
            self.kochi_id = self.kochi.id
            self.buyer_ids = [buyer.id for buyer in buyers]

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def login(self):
        self.client.post("/api/auth/register", json={
            "username": "mvp-user",
            "email": "mvp-user@example.test",
            "password": "test-password",
        })
        response = self.client.post("/api/auth/login", json={
            "email": "mvp-user@example.test",
            "password": "test-password",
        })
        self.assertEqual(response.status_code, 200)
        return {"Origin": "http://localhost:5173"}

    def test_harbours_and_dashboard(self):
        response = self.client.get("/api/harbours")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()["harbours"]), 3)
        dashboard = self.client.get(f"/api/harbours/{self.kochi_id}/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.get_json()["harbour"]["name"], "Kochi")
        self.assertEqual(len(dashboard.get_json()["active_auctions"]), 1)

    def test_prices_and_comparison_have_provenance(self):
        response = self.client.get("/api/market/prices")
        self.assertEqual(response.status_code, 200)
        first_price = response.get_json()["prices"][0]
        self.assertEqual(first_price["source"], "DEMO")
        self.assertEqual(first_price["freshness"], "HISTORICAL")
        self.assertTrue(first_price["is_demo_data"])
        self.assertNotEqual(first_price["freshness"], "LIVE")
        comparison = self.client.get(
            f"/api/market/compare?species_id={self.species_id}&harbour_id={self.kochi_id}&quantity_kg=500"
        )
        self.assertEqual(comparison.status_code, 200)
        self.assertEqual(len(comparison.get_json()["markets"]), 3)

    def test_decision_is_deterministic_and_explainable(self):
        payload = {
            "species_id": self.species_id,
            "quantity_kg": 500,
            "current_harbour_id": self.kochi_id,
        }
        first = self.client.post("/api/decision/recommend", json=payload)
        second = self.client.post("/api/decision/recommend", json=payload)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.get_json(), second.get_json())
        self.assertEqual(first.get_json()["recommendation"]["harbour"], "Kochi")
        self.assertEqual(set(first.get_json()["factors"]), {
            "price", "demand", "buyers", "resources", "freshness",
        })

    def test_invalid_input_returns_json_error(self):
        response = self.client.post("/api/decision/recommend", json={
            "species_id": self.species_id,
            "quantity_kg": -2,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())
        missing = self.client.get("/api/harbours/99999")
        self.assertEqual(missing.status_code, 404)
        self.assertIn("error", missing.get_json())
        invalid_species = self.client.post("/api/decision/recommend", json={
            "species_id": 99999, "quantity_kg": 10,
        })
        self.assertEqual(invalid_species.status_code, 404)
        invalid_harbour = self.client.get("/api/harbours/99999/dashboard")
        self.assertEqual(invalid_harbour.status_code, 404)
        zero_quantity = self.client.post("/api/decision/recommend", json={
            "species_id": self.species_id, "quantity_kg": 0,
        })
        self.assertEqual(zero_quantity.status_code, 400)

    def test_ai_is_cleanly_unavailable_without_key(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            response = self.client.post("/api/ai/assistant", json={
                "harbour_id": self.kochi_id,
                "message": "Where should I sell 500kg sardines?",
            })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["available"])

    def test_ai_uses_backend_context_without_live_provider_call(self):
        class FakeProvider:
            def explain(self, question, structured_context):
                self.context = structured_context
                return "Based on the supplied prototype data, compare the available options."

        fake_provider = FakeProvider()
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch("app.ai.routes.GeminiProvider", return_value=fake_provider):
                response = self.client.post("/api/ai/assistant", json={
                    "harbour_id": self.kochi_id,
                    "message": "Where should I sell 500kg sardines?",
                })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["available"])
        self.assertIn("deterministic_recommendation", fake_provider.context)
        self.assertTrue(fake_provider.context["deterministic_recommendation"]["is_demo_data"])

    def test_ai_provider_failure_returns_fallback(self):
        class FailingProvider:
            def explain(self, question, structured_context):
                raise TimeoutError("simulated provider timeout")

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch("app.ai.routes.GeminiProvider", return_value=FailingProvider()):
                response = self.client.post("/api/ai/assistant", json={
                    "harbour_id": self.kochi_id,
                    "message": "Summarize current harbour conditions.",
                })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["available"])
        self.assertEqual(
            response.get_json()["message"],
            "AI assistant is temporarily unavailable.",
        )

    def test_auction_create_bid_close_flow_and_auth(self):
        payload = {
            "harbour_id": self.kochi_id,
            "species_id": self.species_id,
            "quantity_kg": 500,
            "starting_price": 170,
            "quality_grade": "A",
        }
        unauthenticated = self.client.post("/api/auctions", json=payload)
        self.assertEqual(unauthenticated.status_code, 401)
        headers = self.login()
        created = self.client.post("/api/auctions", json=payload, headers=headers)
        self.assertEqual(created.status_code, 201)
        auction_id = created.get_json()["auction"]["id"]
        below = self.client.post(f"/api/auctions/{auction_id}/bids", json={
            "buyer_id": self.buyer_ids[1], "amount": 170,
        }, headers=headers)
        self.assertEqual(below.status_code, 400)
        missing_buyer = self.client.post(f"/api/auctions/{auction_id}/bids", json={
            "buyer_id": 99999, "amount": 180,
        }, headers=headers)
        self.assertEqual(missing_buyer.status_code, 404)
        missing_auction = self.client.post("/api/auctions/99999/bids", json={
            "buyer_id": self.buyer_ids[1], "amount": 180,
        }, headers=headers)
        self.assertEqual(missing_auction.status_code, 404)
        first = self.client.post(f"/api/auctions/{auction_id}/bids", json={
            "buyer_id": self.buyer_ids[1], "amount": 175,
        }, headers=headers)
        second = self.client.post(f"/api/auctions/{auction_id}/bids", json={
            "buyer_id": self.buyer_ids[2], "amount": 181,
        }, headers=headers)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.get_json()["auction"]["current_price"], 181)
        closed = self.client.post(f"/api/auctions/{auction_id}/close", headers=headers)
        self.assertEqual(closed.status_code, 200)
        self.assertEqual(closed.get_json()["auction"]["status"], "CLOSED")
        self.assertEqual(closed.get_json()["auction"]["winner"]["id"], self.buyer_ids[2])
        fetched = self.client.get(f"/api/auctions/{auction_id}")
        self.assertEqual(fetched.get_json()["auction"]["status"], "CLOSED")
        self.assertEqual(fetched.get_json()["auction"]["current_price"], 181)
        rejected = self.client.post(f"/api/auctions/{auction_id}/bids", json={
            "buyer_id": self.buyer_ids[1], "amount": 190,
        }, headers=headers)
        self.assertEqual(rejected.status_code, 409)

    def test_demand_and_resource_mutations_validate_capacity(self):
        headers = self.login()
        created = self.client.post(f"/api/buyers/{self.buyer_ids[1]}/demand", json={
            "species_id": self.species_id,
            "requested_quantity_kg": 100,
        }, headers=headers)
        self.assertEqual(created.status_code, 201)
        demand_id = created.get_json()["demand"]["id"]
        invalid = self.client.patch(f"/api/buyers/demand/{demand_id}", json={
            "fulfilled_quantity_kg": 101,
        }, headers=headers)
        self.assertEqual(invalid.status_code, 400)
        updated = self.client.patch(f"/api/buyers/demand/{demand_id}", json={
            "fulfilled_quantity_kg": 40,
        }, headers=headers)
        self.assertEqual(updated.get_json()["demand"]["remaining_quantity_kg"], 60)
        self.assertEqual(updated.get_json()["demand"]["status"], "PARTIAL")

        over_capacity = self.client.patch(f"/api/resources/{self.kochi_id}/ice", json={
            "available_tonnes": 1000,
        }, headers=headers)
        self.assertEqual(over_capacity.status_code, 400)
        ice = self.client.patch(f"/api/resources/{self.kochi_id}/ice", json={
            "available_tonnes": 20,
        }, headers=headers)
        self.assertEqual(ice.status_code, 200)
        self.assertEqual(ice.get_json()["ice"]["source"], "HARBOUR_OPERATOR")
        storage = self.client.patch(f"/api/resources/{self.kochi_id}/storage", json={
            "occupied_tonnes": 80,
            "reserved_tonnes": 10,
        }, headers=headers)
        self.assertEqual(storage.status_code, 200)
        self.assertEqual(storage.get_json()["cold_storage"]["available_tonnes"], 10)
        invalid_storage = self.client.patch(f"/api/resources/{self.kochi_id}/storage", json={
            "occupied_tonnes": 99,
            "reserved_tonnes": 2,
        }, headers=headers)
        self.assertEqual(invalid_storage.status_code, 400)

    def test_announcement_alert_and_health(self):
        headers = self.login()
        me = self.client.get("/api/auth/me")
        self.assertEqual(me.status_code, 200)
        denied_origin = self.client.post("/api/announcements", json={
            "title": "blocked", "message": "blocked",
        }, headers={"Origin": "https://untrusted.example"})
        self.assertEqual(denied_origin.status_code, 403)
        announcement = self.client.post("/api/announcements", json={
            "harbour_id": self.kochi_id,
            "title": "Auction window",
            "message": "Auction opens at 11:00.",
            "priority": "HIGH",
        }, headers=headers)
        self.assertEqual(announcement.status_code, 201)
        self.assertEqual(announcement.get_json()["announcement"]["source"], "HARBOUR_OPERATOR")
        alert = self.client.post("/api/alerts", json={
            "harbour_id": self.kochi_id,
            "type": "AUCTION_DELAY",
            "title": "Auction delayed",
            "message": "Auction will begin later.",
        }, headers=headers)
        self.assertEqual(alert.status_code, 201)
        self.assertEqual(alert.get_json()["alert"]["active"], True)
        health = self.client.get("/api/health")
        self.assertEqual(health.get_json(), {"status": "ok", "service": "harbour-os"})

    def test_decision_handles_no_market_and_missing_factors(self):
        no_price_app = self.app
        with no_price_app.app_context():
            db.session.query(FishPrice).delete()
            db.session.commit()
        no_market = self.client.post("/api/decision/recommend", json={
            "species_id": self.species_id, "quantity_kg": 500,
        })
        self.assertEqual(no_market.status_code, 404)
        self.assertEqual(no_market.get_json()["error"]["code"], "no_market_data")

    def test_decision_with_one_harbour_and_missing_resources_is_explained(self):
        with self.app.app_context():
            Harbour.query.filter_by(name="Munambam").update({"status": "CLOSED"})
            Harbour.query.filter_by(name="Beypore").update({"status": "CLOSED"})
            Buyer.query.update({"status": "INACTIVE"})
            db.session.query(IcePlant).delete()
            db.session.query(ColdStorage).delete()
            db.session.commit()
        response = self.client.post("/api/decision/recommend", json={
            "species_id": self.species_id, "quantity_kg": 500,
            "current_harbour_id": self.kochi_id,
        })
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(len(result["markets_considered"]), 1)
        self.assertTrue(any("No active buyers" in item for item in result["cautions"]))
        self.assertTrue(any("Buyer demand data is unavailable" in item for item in result["cautions"]))
        self.assertTrue(any("Ice or cold storage" in item for item in result["cautions"]))
        self.assertEqual(result["data_freshness"], "HISTORICAL")


if __name__ == "__main__":
    unittest.main()
