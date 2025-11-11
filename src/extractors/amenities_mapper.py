from dataclasses import asdict
from typing import Any, Dict, List

from .listing_parser import Listing

# Simple amenity taxonomy for demonstration purposes.
AMENITY_CATEGORY_MAP: Dict[str, Dict[str, str]] = {
    "wifi": {"category": "Connectivity", "icon": "wifi"},
    "ethernet": {"category": "Connectivity", "icon": "ethernet"},
    "heating": {"category": "Climate", "icon": "thermostat"},
    "air conditioning": {"category": "Climate", "icon": "ac-unit"},
    "washer": {"category": "Appliances", "icon": "local-laundry-service"},
    "dryer": {"category": "Appliances", "icon": "local-laundry-service"},
    "kitchen": {"category": "Kitchen", "icon": "kitchen"},
    "tv": {"category": "Entertainment", "icon": "tv"},
    "cable": {"category": "Entertainment", "icon": "cable"},
    "parking": {"category": "Transport", "icon": "local-parking"},
}

def map_single_amenity(raw_amenity: str) -> Dict[str, Any]:
    key = raw_amenity.strip().lower()
    match = None
    for k, meta in AMENITY_CATEGORY_MAP.items():
        if k in key:
            match = meta
            break

    if match is None:
        match = {"category": "Other", "icon": "check"}

    return {
        "label": raw_amenity,
        "category": match["category"],
        "icon": match["icon"],
    }

def normalize_amenities(raw_amenities: List[Any]) -> List[Dict[str, Any]]:
    """
    Normalize amenities into a consistent structured format.

    Input can be:
    - list of strings
    - list of dicts with at least a "label" field
    """
    normalized: List[Dict[str, Any]] = []

    for item in raw_amenities:
        if isinstance(item, str):
            normalized.append(map_single_amenity(item))
        elif isinstance(item, dict):
            label = item.get("label") or item.get("name")
            if not label:
                continue
            mapped = map_single_amenity(str(label))
            # Merge metadata, giving precedence to explicit fields
            merged = {**mapped, **item}
            normalized.append(merged)

    return normalized

def normalize_amenities_for_listing(listing: Listing) -> None:
    """
    In-place normalization of a Listing's amenities field.
    """
    raw = listing.amenities or []
    listing.amenities = normalize_amenities(raw)