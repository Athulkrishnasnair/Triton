import re

from app.api.errors import APIError
from app.api.errors import APIError
from app.decision.service import recommend
from app.models import FishSpecies
from app.services.market_service import harbour_dashboard


def build_context(harbour_id, message):
    dashboard = harbour_dashboard(harbour_id)
    context = {
        "harbour": dashboard["harbour"],
        "recent_landings": dashboard["recent_landings"],
        "prices": dashboard["prices"],
        "active_auctions": dashboard["active_auctions"],
        "active_buyers": dashboard["active_buyers"],
        "buyer_demand": dashboard["buyer_demand"],
        "ice": dashboard["ice"],
        "cold_storage": dashboard["cold_storage"],
        "active_alerts": dashboard["active_alerts"],
        "data_note": "DEMO rows are fictional prototype data, not live market facts.",
    }
    lowered = message.casefold()
    species = next(
        (
            item for item in FishSpecies.query.order_by(FishSpecies.id).all()
            if re.search(rf"\b{re.escape(item.name.casefold())}s?\b", lowered)
            or item.local_name.casefold().split(" ")[0].split("(")[0] in lowered
        ),
        None,
    )
    quantity_match = re.search(r"\b([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:kg|kilograms?)\b", lowered)
    if species and quantity_match:
        quantity = float(quantity_match.group(1).replace(",", ""))
        if quantity > 0:
            try:
                context["deterministic_recommendation"] = recommend(
                    species.id, quantity, harbour_id
                )
            except APIError:
                context["decision_availability"] = (
                    "A deterministic comparison is unavailable because price observations are missing."
                )
    return context


def ask_assistant(harbour_id, message, provider):
    context = build_context(harbour_id, message)
    try:
        answer = provider.explain(message, context)
    except Exception:
        return {
            "available": False,
            "message": "AI assistant is temporarily unavailable.",
            "context": context,
        }
    return {"available": True, "answer": answer, "context": context}
