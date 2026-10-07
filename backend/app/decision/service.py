"""Deterministic, explainable harbour opportunity scoring."""

from app.api.errors import APIError
from app.services.market_service import compare_markets


WEIGHTS = {
    "price": 0.40,
    "demand": 0.25,
    "buyers": 0.15,
    "resources": 0.10,
    "freshness": 0.10,
}


def _relative_scores(values):
    usable = [float(value) for value in values if value is not None]
    if not usable:
        return [0.0 for _ in values]
    low, high = min(usable), max(usable)
    if high == low:
        equal_score = 0.0 if high == 0 else 70.0
        return [equal_score if value is not None else 0.0 for value in values]
    return [round((float(value) - low) * 100 / (high - low), 2) if value is not None else 0.0 for value in values]


def _recommendation_reasons(market, candidates):
    reasons = []
    prices = [item["price"]["value"] for item in candidates if item.get("price")]
    if (
        len(candidates) > 1
        and market["price"]
        and max(prices) > 0
        and prices.count(market["price"]["value"]) == 1
        and market["price"]["value"] == max(prices)
    ):
        reasons.append(f"Higher indicative {market['species']['name'].lower()} price in available observations.")
    demands = [item["demand"] for item in candidates]
    if len(candidates) > 1 and max(demands) > 0 and demands.count(market["demand"]) == 1 and market["demand"] == max(demands):
        reasons.append("Strongest recorded remaining buyer demand among compared harbours.")
    buyer_counts = [item["active_buyers"] for item in candidates]
    if len(candidates) > 1 and max(buyer_counts) > 0 and buyer_counts.count(market["active_buyers"]) == 1 and market["active_buyers"] == max(buyer_counts):
        reasons.append("Most active buyers associated with this harbour in the available data.")
    return reasons or ["Best weighted score among harbours with usable market data."]


def recommend(species_id, quantity_kg, current_harbour_id=None):
    comparison = compare_markets(species_id, quantity_kg, current_harbour_id)
    candidates = []
    for market in comparison["markets"]:
        price = market["price"]
        if not price:
            continue
        candidates.append({
            **market,
            "species": comparison["species"],
            "demand": market["demand"]["remaining_quantity_kg"],
            "demand_provenance": market["demand"],
        })
    if not candidates:
        raise APIError("No price observations are available for this species.", 404, "no_market_data")

    price_scores = _relative_scores([item["price"]["value"] for item in candidates])
    demand_scores = _relative_scores([item["demand"] for item in candidates])
    buyer_scores = _relative_scores([item["active_buyers"] for item in candidates])

    resource_scores = []
    freshness_scores = []
    for item in candidates:
        amount = quantity_kg
        ice_kg = (item["ice_available"] or 0) * 1000
        storage_kg = (item["storage_available"] or 0) * 1000
        ice_support = min(100, ice_kg * 100 / amount)
        storage_support = min(100, storage_kg * 100 / amount)
        resource_scores.append(round((ice_support + storage_support) / 2, 2))
        freshness_scores.append({
            "LIVE": 100.0,
            "RECENT": 70.0,
            "HISTORICAL": 35.0,
        }.get(item["freshness"], 0.0))

    scored = []
    for index, item in enumerate(candidates):
        factors = {
            "price": price_scores[index],
            "demand": demand_scores[index],
            "buyers": buyer_scores[index],
            "resources": resource_scores[index],
            "freshness": freshness_scores[index],
        }
        score = round(sum(factors[name] * weight for name, weight in WEIGHTS.items()))
        item["factors"] = factors
        item["score"] = max(0, min(100, score))
        scored.append(item)
    scored.sort(key=lambda item: (-item["score"], item["harbour"]["name"]))
    winner = scored[0]
    reasons = _recommendation_reasons(winner, candidates)
    cautions = [
        "Transport and logistics costs are unavailable and are not included in this comparison.",
        "This is an indicative opportunity based on available data, not a profit guarantee.",
    ]
    if winner["is_demo_data"]:
        cautions.insert(0, "Market, buyer, landing, and resource figures are fictional prototype data.")
    if any(item["demand_provenance"]["source"] == "UNKNOWN" for item in scored):
        cautions.append("Buyer demand data is unavailable for one or more compared harbours.")
    if any(item["active_buyers"] == 0 for item in scored):
        cautions.append("No active buyers were found for one or more compared harbours.")
    if any(
        item["ice_available"] is None
        or item["storage_available"] is None
        or item["ice_status"] == "CLOSED"
        or item["storage_status"] == "CLOSED"
        for item in scored
    ):
        cautions.append("Ice or cold storage data is missing for one or more compared harbours.")
    if winner["freshness"] == "HISTORICAL":
        cautions.append("Market or resource observations are historical; confirm current conditions before acting.")
    if winner["storage_available"] is None or winner["storage_available"] * 1000 < quantity_kg:
        cautions.append("Reported cold storage may not accommodate the full quantity.")
    comparable_storage = [
        item["storage_available"] for item in scored
        if item["storage_available"] is not None
    ]
    if comparable_storage and winner["storage_available"] < max(comparable_storage):
        cautions.append("Storage availability is lower than at another compared harbour.")
    if current_harbour_id is not None and winner["harbour"]["id"] != current_harbour_id:
        cautions.append("The recommended harbour differs from your current harbour; travel feasibility is unknown.")

    return {
        "recommendation": {
            "harbour": winner["harbour"]["name"],
            "harbour_id": winner["harbour"]["id"],
            "score": winner["score"],
            "label": "best current opportunity",
        },
        "species": comparison["species"],
        "quantity_kg": quantity_kg,
        "factors": winner["factors"],
        "reasons": reasons,
        "cautions": cautions,
        "data_freshness": winner["freshness"],
        "is_demo": winner["is_demo_data"],
        "is_demo_data": winner["is_demo_data"],
        "weighting": WEIGHTS,
        "markets_considered": [
            {
                "harbour": item["harbour"]["name"],
                "score": item["score"],
                "factors": item["factors"],
            }
            for item in scored
        ],
    }
