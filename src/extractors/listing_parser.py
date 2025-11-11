from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

@dataclass
class Rating:
    accuracy: Optional[float] = None
    cleanliness: Optional[float] = None
    communication: Optional[float] = None
    location: Optional[float] = None
    value: Optional[float] = None
    reviewsCount: Optional[int] = None

@dataclass
class Host:
    name: str
    profileImage: Optional[str] = None
    highlights: Optional[List[str]] = None

@dataclass
class Price:
    label: str
    totalBeforeTaxes: Optional[str] = None

@dataclass
class Coordinates:
    latitude: float
    longitude: float

@dataclass
class LocationDescription:
    title: str
    content: str

@dataclass
class Listing:
    id: str
    coordinates: Coordinates
    title: str
    url: str
    roomType: Optional[str] = None
    isSuperHost: Optional[bool] = None
    personCapacity: Optional[int] = None
    rating: Optional[Rating] = None
    host: Optional[Host] = None
    price: Optional[Price] = None
    amenities: Optional[List[Any]] = None
    locationDescriptions: Optional[List[LocationDescription]] = None
    description: Optional[str] = None

    @staticmethod
    def _parse_coordinates(raw: Dict[str, Any]) -> Coordinates:
        return Coordinates(
            latitude=float(raw.get("latitude", 0.0)),
            longitude=float(raw.get("longitude", 0.0)),
        )

    @staticmethod
    def _parse_rating(raw: Optional[Dict[str, Any]]) -> Optional[Rating]:
        if raw is None:
            return None
        return Rating(
            accuracy=raw.get("accuracy"),
            cleanliness=raw.get("cleanliness"),
            communication=raw.get("communication"),
            location=raw.get("location"),
            value=raw.get("value"),
            reviewsCount=raw.get("reviewsCount"),
        )

    @staticmethod
    def _parse_host(raw: Optional[Dict[str, Any]]) -> Optional[Host]:
        if raw is None:
            return None
        return Host(
            name=raw.get("name", "Unknown host"),
            profileImage=raw.get("profileImage"),
            highlights=raw.get("highlights") or [],
        )

    @staticmethod
    def _parse_price(raw: Optional[Dict[str, Any]]) -> Optional[Price]:
        if raw is None:
            return None
        return Price(
            label=raw.get("label", ""),
            totalBeforeTaxes=raw.get("totalBeforeTaxes"),
        )

    @staticmethod
    def _parse_location_descriptions(
        raw_list: Optional[List[Dict[str, Any]]]
    ) -> Optional[List[LocationDescription]]:
        if not raw_list:
            return None
        return [
            LocationDescription(
                title=item.get("title", ""),
                content=item.get("content", ""),
            )
            for item in raw_list
        ]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Listing":
        coordinates = cls._parse_coordinates(data.get("coordinates") or {})
        rating = cls._parse_rating(data.get("rating"))
        host = cls._parse_host(data.get("host"))
        price = cls._parse_price(data.get("price"))
        loc_desc = cls._parse_location_descriptions(data.get("locationDescriptions"))

        return cls(
            id=str(data.get("id")),
            coordinates=coordinates,
            title=data.get("title", ""),
            url=data.get("url", ""),
            roomType=data.get("roomType"),
            isSuperHost=data.get("isSuperHost"),
            personCapacity=data.get("personCapacity"),
            rating=rating,
            host=host,
            price=price,
            amenities=data.get("amenities") or [],
            locationDescriptions=loc_desc,
            description=data.get("description"),
        )

class ListingParser:
    """
    Responsible for reading listing data from JSON and transforming it
    into strongly typed Listing objects.
    """

    def load_listings_from_file(self, path: Path) -> List[Listing]:
        if not path.exists():
            raise FileNotFoundError(f"Listings file not found at: {path}")

        with path.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)

        if not isinstance(raw_data, list):
            raise ValueError(
                f"Expected list of listings in JSON file, got {type(raw_data)} instead."
            )

        listings: List[Listing] = []
        for item in raw_data:
            if not isinstance(item, dict):
                continue
            try:
                listing = Listing.from_dict(item)
                listings.append(listing)
            except Exception as exc:
                # Skip malformed items but do not stop processing
                # In a real-world application, this would be logged.
                print(f"Skipping malformed listing: {exc}")

        return listings