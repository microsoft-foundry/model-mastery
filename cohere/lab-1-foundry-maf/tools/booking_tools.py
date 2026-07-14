"""Mock booking tools for Lab 1's enterprise travel concierge agent.

The functions in this module deliberately use local JSON catalogs instead of live
supplier APIs. In the workshop, Foundry exposes their signatures and docstrings
to Command A as function-calling tools, then the notebook executes the selected
Python function client-side and sends the result back to the agent.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Catalog paths are module-relative so tool calls work from notebooks, tests, or the load script.
CATALOG_DIR = Path(__file__).resolve().parents[1] / "data" / "catalogs"


def _load_catalog(name: str) -> list[dict[str, Any]]:
    """Read a catalog file from data/catalogs and return its list of records."""
    with (CATALOG_DIR / name).open(encoding="utf-8") as handle:
        data = json.load(handle)
    # A list shape keeps tool outputs predictable for the agent and evaluation traces.
    if not isinstance(data, list):
        raise ValueError(f"Catalog {name} must contain a JSON list")
    return data


# Treat a missing budget as unconstrained, but enforce numeric caps when policy or the traveler provides one.
def _money_at_or_below(value: float | int, limit: float | int | None) -> bool:
    return limit is None or float(value) <= float(limit)


def search_flights(
    origin: str,
    destination: str,
    depart_date: str,
    return_date: str | None = None,
    max_price: float | None = None,
) -> list[dict[str, Any]]:
    """Search corporate flight options by route, date, and optional price cap.

    Args:
        origin: Three-letter airport code for the departure airport, such as
            ``SFO`` or ``SEA``. Matching is case-insensitive.
        destination: Three-letter airport code for the arrival airport.
        depart_date: Outbound travel date in ``YYYY-MM-DD`` format.
        return_date: Optional return date in ``YYYY-MM-DD`` format. When set,
            round-trip records must match this date.
        max_price: Optional maximum total fare in USD. Use this when the
            traveler gives a budget or when policy requires a lower-cost nudge.

    Returns:
        A list of matching flight dictionaries sorted by price. Each result
        includes carrier, cabin, duration, fare, refundable flag, and a policy
        hint explaining whether the option is preferred or needs a nudge.
    """
    # Normalize airport codes once so catalog matching is case-insensitive.
    origin_code = origin.upper()
    destination_code = destination.upper()
    results = []
    # Booking validates the selected id against the same catalog used for search.
    for flight in _load_catalog("flights.json"):
        if flight["origin"].upper() != origin_code:
            continue
        if flight["destination"].upper() != destination_code:
            continue
        if flight["depart_date"] != depart_date:
            continue
        # One-way searches omit return_date; round-trip searches must match both legs.
        if return_date and flight.get("return_date") != return_date:
            continue
        if not _money_at_or_below(flight["price_usd"], max_price):
            continue
        results.append(flight)
    # Sort by cost first because the corporate policy nudges toward lower fares.
    return sorted(results, key=lambda item: (item["price_usd"], item["duration_minutes"]))


def book_flight(flight_id: str, traveler_name: str, cost_center: str | None = None) -> dict[str, Any]:
    """Create a mock flight booking confirmation for an option from search_flights.

    Use this only after the traveler has selected, or clearly accepted, a flight
    option. The function does not charge a card or call an airline; it returns a
    realistic confirmation payload that can be shown in the lab transcript.
    """
    for flight in _load_catalog("flights.json"):
        if flight["id"] == flight_id:
            return {
                "confirmation_number": f"FL-{flight_id.upper()}-MM",
                "status": "confirmed",
                "traveler_name": traveler_name,
                "cost_center": cost_center,
                "booking_type": "flight",
                "details": flight,
            }
    raise ValueError(f"Unknown flight_id: {flight_id}")


def search_hotels(
    city: str,
    check_in: str,
    check_out: str,
    max_nightly_rate: float | None = None,
) -> list[dict[str, Any]]:
    """Search hotel options by city, stay dates, and nightly-rate cap.

    Args:
        city: Destination city, for example ``Seattle`` or ``New York``.
        check_in: Arrival date in ``YYYY-MM-DD`` format.
        check_out: Departure date in ``YYYY-MM-DD`` format.
        max_nightly_rate: Optional nightly rate cap in USD. Apply the corporate
            policy cap when the traveler asks for a city or tier with a limit.

    Returns:
        Matching hotel dictionaries sorted by nightly rate and distance to the
        business district. Results include amenities, city tier, refundable flag,
        and a policy hint that helps the concierge explain compliant choices.
    """
    # casefold handles city matching more robustly than lower() for user-entered text.
    normalized_city = city.casefold()
    results = []
    # Confirmation payloads are deterministic so repeated demos and evaluations are comparable.
    for hotel in _load_catalog("hotels.json"):
        if hotel["city"].casefold() != normalized_city:
            continue
        # ISO date strings compare lexicographically, so no datetime parsing is needed for these catalogs.
        if check_in < hotel["available_from"] or check_out > hotel["available_to"]:
            continue
        if not _money_at_or_below(hotel["nightly_rate_usd"], max_nightly_rate):
            continue
        results.append(hotel)
    # Rate then distance mirrors how a travel desk narrows compliant hotel choices.
    return sorted(results, key=lambda item: (item["nightly_rate_usd"], item["distance_to_downtown_miles"]))


def book_hotel(hotel_id: str, traveler_name: str, cost_center: str | None = None) -> dict[str, Any]:
    """Create a mock hotel booking confirmation for an option from search_hotels.

    Call this only after the traveler has accepted a hotel. The return value is a
    deterministic confirmation object suitable for demos and evaluation traces.
    """
    for hotel in _load_catalog("hotels.json"):
        if hotel["id"] == hotel_id:
            return {
                "confirmation_number": f"HT-{hotel_id.upper()}-MM",
                "status": "confirmed",
                "traveler_name": traveler_name,
                "cost_center": cost_center,
                "booking_type": "hotel",
                "details": hotel,
            }
    raise ValueError(f"Unknown hotel_id: {hotel_id}")


def search_cars(
    city: str,
    pickup_date: str,
    dropoff_date: str,
    class_: str | None = None,
) -> list[dict[str, Any]]:
    """Search rental cars by city, dates, and optional car class.

    Args:
        city: Pickup city, such as ``Miami`` or ``Chicago``.
        pickup_date: Pickup date in ``YYYY-MM-DD`` format.
        dropoff_date: Drop-off date in ``YYYY-MM-DD`` format.
        class_: Optional car class such as ``economy``, ``standard``, ``suv``, or
            ``luxury``. Prefer ``economy`` or ``standard`` unless a policy
            exception is justified.

    Returns:
        Matching car dictionaries sorted by daily rate. Each record includes the
        supplier, class, transmission, daily rate, and a policy hint.
    """
    normalized_city = city.casefold()
    # The trailing underscore avoids shadowing Python's class keyword while keeping the tool schema readable.
    normalized_class = class_.casefold() if class_ else None
    results = []
    # Keep car bookings local-only; the confirmation is a teaching artifact, not a supplier transaction.
    for car in _load_catalog("cars.json"):
        if car["city"].casefold() != normalized_city:
            continue
        if pickup_date < car["available_from"] or dropoff_date > car["available_to"]:
            continue
        # Class is optional: omit it to let the agent show compliant economy/standard alternatives.
        if normalized_class and car["class"].casefold() != normalized_class:
            continue
        results.append(car)
    # Cheapest-first ordering makes policy-friendly options easiest for the model to explain.
    return sorted(results, key=lambda item: item["daily_rate_usd"])


def book_car(car_id: str, traveler_name: str, cost_center: str | None = None) -> dict[str, Any]:
    """Create a mock rental-car booking confirmation for an option from search_cars.

    Use this only after the traveler accepts the vehicle and any policy nudge has
    been handled. The confirmation is local-only and safe for repeated demos.
    """
    for car in _load_catalog("cars.json"):
        if car["id"] == car_id:
            return {
                "confirmation_number": f"RC-{car_id.upper()}-MM",
                "status": "confirmed",
                "traveler_name": traveler_name,
                "cost_center": cost_center,
                "booking_type": "car",
                "details": car,
            }
    raise ValueError(f"Unknown car_id: {car_id}")
