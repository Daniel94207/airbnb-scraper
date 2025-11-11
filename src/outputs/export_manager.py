import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List
from xml.etree.ElementTree import Element, SubElement, ElementTree

class ExportManager:
    def __init__(self, output_dir: Path, base_filename: str = "airbnb_listings") -> None:
        self.output_dir = output_dir
        self.base_filename = base_filename

    # Public API -------------------------------------------------------------

    def export_all(self, listings: List[Dict[str, Any]], formats: Iterable[str]) -> None:
        formats = {fmt.lower().strip() for fmt in formats}
        if "json" in formats:
            self.export_json(listings)
        if "csv" in formats:
            self.export_csv(listings)
        if "xml" in formats:
            self.export_xml(listings)
        if "rss" in formats:
            self.export_rss(listings)
        if "html" in formats:
            self.export_html_table(listings)

    # Helpers ----------------------------------------------------------------

    def _path(self, suffix: str) -> Path:
        return self.output_dir / f"{self.base_filename}.{suffix}"

    # JSON -------------------------------------------------------------------

    def export_json(self, listings: List[Dict[str, Any]]) -> Path:
        path = self._path("json")
        with path.open("w", encoding="utf-8") as f:
            json.dump(listings, f, ensure_ascii=False, indent=2)
        return path

    # CSV --------------------------------------------------------------------

    def export_csv(self, listings: List[Dict[str, Any]]) -> Path:
        path = self._path("csv")

        # Flatten a subset of fields that make sense for CSV output.
        fieldnames = [
            "id",
            "title",
            "url",
            "roomType",
            "isSuperHost",
            "personCapacity",
            "price.label",
            "price.totalBeforeTaxes",
            "rating.reviewsCount",
            "host.name",
            "coordinates.latitude",
            "coordinates.longitude",
        ]

        def flatten(listing: Dict[str, Any]) -> Dict[str, Any]:
            def get_nested(obj: Dict[str, Any], path: str) -> Any:
                parts = path.split(".")
                current: Any = obj
                for p in parts:
                    if current is None:
                        return None
                    if not isinstance(current, dict):
                        return None
                    current = current.get(p)
                return current

            flat: Dict[str, Any] = {}
            for name in fieldnames:
                flat[name] = get_nested(listing, name)
            return flat

        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for listing in listings:
                writer.writerow(flatten(listing))

        return path

    # XML --------------------------------------------------------------------

    def export_xml(self, listings: List[Dict[str, Any]]) -> Path:
        path = self._path("xml")

        root = Element("listings")
        for listing in listings:
            listing_el = SubElement(root, "listing", attrib={"id": str(listing.get("id", ""))})
            SubElement(listing_el, "title").text = str(listing.get("title", ""))
            SubElement(listing_el, "url").text = str(listing.get("url", ""))

            coordinates = listing.get("coordinates") or {}
            coords_el = SubElement(listing_el, "coordinates")
            SubElement(coords_el, "latitude").text = str(coordinates.get("latitude", ""))
            SubElement(coords_el, "longitude").text = str(coordinates.get("longitude", ""))

            price = listing.get("price") or {}
            price_el = SubElement(listing_el, "price")
            SubElement(price_el, "label").text = str(price.get("label", ""))
            SubElement(price_el, "totalBeforeTaxes").text = str(price.get("totalBeforeTaxes", ""))

            rating = listing.get("rating") or {}
            rating_el = SubElement(listing_el, "rating")
            for key, value in rating.items():
                SubElement(rating_el, key).text = str(value)

            host = listing.get("host") or {}
            host_el = SubElement(listing_el, "host")
            SubElement(host_el, "name").text = str(host.get("name", ""))
            SubElement(host_el, "profileImage").text = str(host.get("profileImage", ""))
            highlights = host.get("highlights") or []
            highlights_el = SubElement(host_el, "highlights")
            for h in highlights:
                SubElement(highlights_el, "highlight").text = str(h)

            amenities = listing.get("amenities") or []
            amenities_el = SubElement(listing_el, "amenities")
            for amenity in amenities:
                if isinstance(amenity, dict):
                    amen_el = SubElement(amenities_el, "amenity")
                    SubElement(amen_el, "label").text = str(amenity.get("label", ""))
                    SubElement(amen_el, "category").text = str(amenity.get("category", ""))
                    SubElement(amen_el, "icon").text = str(amenity.get("icon", ""))
                else:
                    SubElement(amenities_el, "amenity").text = str(amenity)

        tree = ElementTree(root)
        tree.write(path, encoding="utf-8", xml_declaration=True)
        return path

    # RSS --------------------------------------------------------------------

    def export_rss(self, listings: List[Dict[str, Any]]) -> Path:
        path = self._path("rss")

        rss = Element("rss", attrib={"version": "2.0"})
        channel = SubElement(rss, "channel")
        SubElement(channel, "title").text = "Airbnb Listings Feed"
        SubElement(channel, "description").text = (
            "RSS feed generated from Airbnb listing data."
        )
        SubElement(channel, "link").text = "https://www.airbnb.com"
        SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        )

        for listing in listings:
            item = SubElement(channel, "item")
            SubElement(item, "title").text = str(listing.get("title", ""))
            SubElement(item, "link").text = str(listing.get("url", ""))
            SubElement(item, "guid").text = str(listing.get("id", ""))

            price = listing.get("price") or {}
            host = listing.get("host") or {}
            description_parts = [
                f"Price: {price.get('label', 'N/A')}",
                f"Host: {host.get('name', 'Unknown')}",
            ]
            SubElement(item, "description").text = " | ".join(description_parts)

        tree = ElementTree(rss)
        tree.write(path, encoding="utf-8", xml_declaration=True)
        return path

    # HTML -------------------------------------------------------------------

    def export_html_table(self, listings: List[Dict[str, Any]]) -> Path:
        path = self._path("html")

        def escape(text: Any) -> str:
            s = str(text)
            return (
                s.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
            )

        rows: List[str] = []
        for listing in listings:
            price = (listing.get("price") or {}).get("label", "")
            host = (listing.get("host") or {}).get("name", "")
            rating = (listing.get("rating") or {}).get("reviewsCount", "")
            row = (
                "<tr>"
                f"<td>{escape(listing.get('id', ''))}</td>"
                f"<td>{escape(listing.get('title', ''))}</td>"
                f"<td><a href=\"{escape(listing.get('url', ''))}\">Link</a></td>"
                f"<td>{escape(price)}</td>"
                f"<td>{escape(host)}</td>"
                f"<td>{escape(rating)}</td>"
                "</tr>"
            )
            rows.append(row)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Airbnb Listings</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 0.5rem; text-align: left; }}
    th {{ background-color: #f4f4f4; }}
    tr:nth-child(even) {{ background-color: #fafafa; }}
  </style>
</head>
<body>
  <h1>Airbnb Listings</h1>
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>Title</th>
        <th>URL</th>
        <th>Price</th>
        <th>Host</th>
        <th>Reviews</th>
      </tr>
    </thead>
    <tbody>
      {"".join(rows)}
    </tbody>
  </table>
</body>
</html>
"""

        with path.open("w", encoding="utf-8") as f:
            f.write(html)

        return path