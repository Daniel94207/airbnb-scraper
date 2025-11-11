import argparse
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from extractors.listing_parser import ListingParser, Listing
from extractors.amenities_mapper import normalize_amenities_for_listing
from outputs.export_manager import ExportManager

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = BASE_DIR / "src" / "config" / "settings.example.json"
DATA_DIR = BASE_DIR / "data"

def setup_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

def load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)
    return config

def apply_amenities_mapping(listings: List[Listing]) -> List[Listing]:
    for listing in listings:
        normalize_amenities_for_listing(listing)
    return listings

def listings_to_primitive(listings: List[Listing]) -> List[Dict[str, Any]]:
    return [asdict(l) for l in listings]

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Airbnb Scraper - process and export Airbnb listing data."
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to settings JSON file (defaults to settings.example.json).",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    config = load_config(config_path)

    setup_logging(config.get("log_level", "INFO"))
    logger = logging.getLogger("airbnb-scraper")

    input_listings_path = Path(config.get("input_listings_path", "")).resolve()
    if not input_listings_path.is_file():
        # Fall back to default sample data if config path is invalid
        input_listings_path = DATA_DIR / "listings.sample.json"
        logger.warning(
            "Configured listings path not found. Falling back to %s",
            input_listings_path,
        )

    output_dir = Path(config.get("output_dir", DATA_DIR / "outputs")).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    export_formats = config.get(
        "export_formats", ["json", "csv", "xml", "rss", "html"]
    )

    logger.info("Using input listings file: %s", input_listings_path)
    logger.info("Output directory: %s", output_dir)
    logger.info("Export formats: %s", ", ".join(export_formats))

    # Parse listings
    parser_instance = ListingParser()
    try:
        listings = parser_instance.load_listings_from_file(input_listings_path)
    except Exception as exc:
        logger.exception("Failed to parse listings file: %s", exc)
        raise SystemExit(1)

    if not listings:
        logger.warning("No listings found in %s", input_listings_path)
        raise SystemExit(0)

    logger.info("Parsed %d listings", len(listings))

    # Apply amenities mapping
    listings = apply_amenities_mapping(listings)
    primitive_listings = listings_to_primitive(listings)

    # Export
    exporter = ExportManager(output_dir=output_dir, base_filename="airbnb_listings")
    try:
        exporter.export_all(primitive_listings, export_formats)
    except Exception as exc:
        logger.exception("Failed to export listings: %s", exc)
        raise SystemExit(1)

    logger.info("Export completed successfully.")

if __name__ == "__main__":
    main()