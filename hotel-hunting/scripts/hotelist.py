#!/usr/bin/env python3
"""Reproducible Hotelist acquisition with honest failure modes.

Examples:
  python3 hotelist.py search "Athens, Greece" --limit 5 --json
  python3 hotelist.py search Springfield --country US --limit 5
  python3 hotelist.py search --lat 37.98 --lng 23.73 --radius-km 8
  python3 hotelist.py detail ONATHDOL --json
  python3 hotelist.py city athens --json

Hotelist endpoints are public but unofficial implementation details. Requests
are sequential, cached, and retried only for transient failures.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

BASE = "https://hotelist.com"
PHOTON = "https://photon.komoot.io/api/"
UA = {
    "User-Agent": "hotel-hunting-skill/3.0 (+https://github.com/sliday/skills)",
    "X-Requested-With": "XMLHttpRequest",
}
CACHE_DIR = Path(os.environ.get("HOTELIST_CACHE_DIR", Path.home() / ".cache" / "hotel-hunting"))
_LAST_REQUEST = 0.0


class HotelistError(RuntimeError):
    pass


class AmbiguousPlace(HotelistError):
    def __init__(self, place: str, candidates: list[dict[str, Any]]):
        super().__init__(f"ambiguous place: {place}")
        self.place = place
        self.candidates = candidates


def _cache_key(url: str, body: bytes | None) -> Path:
    digest = hashlib.sha256(url.encode() + b"\0" + (body or b"")).hexdigest()
    return CACHE_DIR / f"{digest}.txt"


def _request(
    url: str,
    *,
    data: dict[str, Any] | None = None,
    max_age: int = 3600,
    retries: int = 2,
    min_interval: float = 0.35,
) -> str:
    global _LAST_REQUEST
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    path = _cache_key(url, body)
    if max_age >= 0 and path.exists() and time.time() - path.stat().st_mtime <= max_age:
        return path.read_text(encoding="utf-8")

    headers = dict(UA)
    if body is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    for attempt in range(retries + 1):
        wait = min_interval - (time.monotonic() - _LAST_REQUEST)
        if wait > 0:
            time.sleep(wait)
        try:
            req = urllib.request.Request(url, data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                text = response.read().decode("utf-8", "replace")
            _LAST_REQUEST = time.monotonic()
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            return text
        except urllib.error.HTTPError as exc:
            _LAST_REQUEST = time.monotonic()
            if exc.code not in {429, 500, 502, 503, 504} or attempt == retries:
                raise HotelistError(f"HTTP {exc.code} for {url}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            _LAST_REQUEST = time.monotonic()
            if attempt == retries:
                raise HotelistError(f"network failure for {url}: {exc}") from exc
        time.sleep(2**attempt)
    raise AssertionError("unreachable")


def _locality_candidate(feature: dict[str, Any]) -> dict[str, Any]:
    props = feature.get("properties") or {}
    coords = (feature.get("geometry") or {}).get("coordinates") or [None, None]
    return {
        "name": props.get("name"),
        "type": props.get("type"),
        "state": props.get("state"),
        "country": props.get("country"),
        "country_code": (props.get("countrycode") or "").upper() or None,
        "lat": coords[1],
        "lng": coords[0],
        "label": ", ".join(
            str(x) for x in [props.get("name"), props.get("state"), props.get("country")] if x
        ),
    }


def geocode(place: str, *, country: str | None = None, pick: int | None = None, max_age: int = 86400) -> dict[str, Any]:
    query = f"{place}, {country}" if country else place
    url = PHOTON + "?" + urllib.parse.urlencode({"q": query, "limit": 12, "lang": "en"})
    features = json.loads(_request(url, max_age=max_age)).get("features") or []
    candidates = [_locality_candidate(f) for f in features]
    candidates = [c for c in candidates if c["lat"] is not None and c["type"] in {"city", "town", "village", "hamlet"}]
    if country:
        wanted = country.casefold()
        filtered = [c for c in candidates if wanted in {(c["country"] or "").casefold(), (c["country_code"] or "").casefold()}]
        if filtered:
            candidates = filtered
    if not candidates:
        raise HotelistError(f"no locality found for: {query}")
    if pick is not None:
        if pick < 1 or pick > len(candidates):
            raise HotelistError(f"--pick must be between 1 and {len(candidates)}")
        return candidates[pick - 1]

    bare = "," not in place and not country
    same_name = [c for c in candidates if (c["name"] or "").casefold() == place.casefold()]
    jurisdictions = {(c["state"], c["country"]) for c in same_name}
    if bare and len(jurisdictions) > 1:
        raise AmbiguousPlace(place, same_name[:8])
    return candidates[0]


def _bbox(lat: float, lng: float, radius_km: float) -> tuple[float, float, float, float]:
    dlat = radius_km / 111.0
    dlng = radius_km / max(20.0, 111.0 * abs(math.cos(math.radians(lat))))
    return lat - dlat, lat + dlat, lng - dlng, lng + dlng


def _hotel_key(hotel: dict[str, Any]) -> str:
    return re.sub(r"[^a-z0-9]", "", str(hotel.get("name") or "").casefold())


def _distance_km(a: dict[str, Any], b: dict[str, Any]) -> float:
    try:
        lat1, lon1, lat2, lon2 = map(float, [a["latitude"], a["longitude"], b["latitude"], b["longitude"]])
    except (KeyError, TypeError, ValueError):
        return 9999.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0 * 2 * math.atan2(math.sqrt(x), math.sqrt(1 - x))


def dedupe(hotels: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    by_name: dict[str, list[dict[str, Any]]] = {}
    for hotel in hotels:
        by_name.setdefault(_hotel_key(hotel), []).append(hotel)
    for group in by_name.values():
        group.sort(key=lambda h: float(h.get("hotellist_rating") or 0), reverse=True)
        primary = group[0]
        kept.append(primary)
        for duplicate in group[1:]:
            warning = {
                "type": "possible_duplicate",
                "name": primary.get("name"),
                "kept_id": primary.get("hotel_id"),
                "other_id": duplicate.get("hotel_id"),
                "kept_score": primary.get("hotellist_rating"),
                "other_score": duplicate.get("hotellist_rating"),
                "distance_km": round(_distance_km(primary, duplicate), 3),
            }
            warnings.append(warning)
            if warning["distance_km"] > 1.0:
                kept.append(duplicate)
                warning["type"] = "same_name_different_location"
    return kept, warnings


def search(
    *,
    place: str | None,
    country: str | None,
    pick: int | None,
    lat: float | None,
    lng: float | None,
    radius_km: float,
    max_price: float | None,
    min_rating: float | None,
    newer_than: int | None,
    limit: int,
    max_age: int,
) -> dict[str, Any]:
    if lat is None or lng is None:
        if not place:
            raise HotelistError("provide PLACE or both --lat and --lng")
        resolved = geocode(place, country=country, pick=pick, max_age=max_age)
        lat, lng = float(resolved["lat"]), float(resolved["lng"])
    else:
        resolved = {"label": f"{lat:.5f}, {lng:.5f}", "lat": lat, "lng": lng, "type": "coordinates"}

    lat_min, lat_max, lng_min, lng_max = _bbox(lat, lng, radius_km)
    data: dict[str, Any] = {}
    index = 0

    def add(target: str, value: Any, kind: str) -> None:
        nonlocal index
        data[f"filters[{index}][target]"] = target
        data[f"filters[{index}][type]"] = kind
        if isinstance(value, dict):
            for key, item in value.items():
                data[f"filters[{index}][value][{key}]"] = item
        else:
            data[f"filters[{index}][value]"] = value
        index += 1

    add("bbox", {"lat_min": lat_min, "lat_max": lat_max, "lng_min": lng_min, "lng_max": lng_max}, "exact-match")
    if max_price is not None:
        add("price", max_price, "less-than")
    if min_rating is not None:
        add("hotellist_rating", min_rating, "greater-than")
    if newer_than is not None:
        add("year_built", newer_than, "greater-than")

    payload = json.loads(_request(BASE + "/", data=data, max_age=max_age))
    if not isinstance(payload.get("hotels"), list):
        raise HotelistError("Hotelist search response no longer contains hotels[]")
    hotels, warnings = dedupe(payload["hotels"])
    hotels.sort(key=lambda h: float(h.get("hotellist_rating") or 0), reverse=True)
    return {
        "resolved_place": resolved,
        "bbox": {"lat_min": lat_min, "lat_max": lat_max, "lng_min": lng_min, "lng_max": lng_max},
        "raw_count": len(payload["hotels"]),
        "deduplicated_count": len(hotels),
        "hotels": hotels[:limit],
        "integrity_warnings": warnings,
        "price_notice": "Hotelist price is a minimum observed figure, not an exact-stay quote.",
    }


def _strip(fragment: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment))).strip()


def detail(hotel_id: str, *, max_age: int) -> dict[str, Any]:
    text = _strip(_request(f"{BASE}/modal/{urllib.parse.quote(hotel_id)}", data={}, max_age=max_age))

    def score(label: str) -> str | None:
        match = re.search(re.escape(label) + r"\s*([0-9]+(?:\.[0-9]+)?)", text)
        return match.group(1) if match else None

    section = re.search(r"Average rating(.*?)About normalized", text, re.S)
    sources: dict[str, str] = {}
    if section:
        for value, name in re.findall(
            r"\*\s*([0-9]+(?:\.[0-9]+)?)\s*(?:[0-9]+\s*[a-z]+ ago \([0-9-]+\)\s*)?"
            r"([A-Z][A-Za-z.]+(?: [A-Za-z.]+)*?)(?=\s*\*|\s*$)",
            section.group(1),
        ):
            sources[name.strip()] = value
    name_match = re.search(r"×\s*[0-9.]+\s*(.+?)\s*Book this hotel", text)
    price_match = re.search(r"Minimum price \$([0-9,]+)", text)
    fragments = re.findall(r"([\U0001F300-\U0001FAFF☀-➿][^\U0001F300-\U0001FAFF☀-➿]{5,120})", text)
    skip = ("Hotelist Score", "AI rating", "Consensus", "Average rating")
    out = {
        "hotel_id": hotel_id,
        "name": name_match.group(1).strip() if name_match else None,
        "hotelist_score": score("Hotelist Score"),
        "ai_photo_score": score("AI rating of photos"),
        "ai_review_score": score("AI rating of reviews"),
        "source_agreement": score("Consensus about rating"),
        "normalized_sources": sources,
        "minimum_observed_price_usd": price_match.group(1) if price_match else None,
        "distance_to_center": (re.search(r"Distance to center\s*([0-9.]+\s*km)", text) or [None, None])[1],
        "hotelist_derived_claims": [f.strip() for f in fragments if not any(k in f for k in skip)][:30],
        "provenance_notice": "Scores and claims are Hotelist-derived unless underlying sources are separately inspected.",
    }
    required = ["hotelist_score", "ai_photo_score", "ai_review_score", "source_agreement"]
    if not any(out[k] for k in required):
        raise HotelistError("detail response shape changed; no score fields parsed")
    return out


def city(slug: str, *, max_age: int) -> dict[str, Any]:
    raw = _request(f"{BASE}/{urllib.parse.quote(slug)}", max_age=max_age)
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)
    if not match:
        raise HotelistError("city page no longer exposes JSON-LD ItemList")
    parsed = json.loads(match.group(1))
    items = parsed.get("itemListElement")
    if not isinstance(items, list):
        raise HotelistError("city JSON-LD no longer contains itemListElement[]")
    return {"slug": slug, "count": len(items), "items": items}


def _print_human(command: str, result: dict[str, Any], limit: int) -> None:
    if command == "search":
        print(f"# {result['resolved_place']['label']} — {result['raw_count']} raw, {result['deduplicated_count']} after name dedupe")
        for hotel in result["hotels"]:
            price = hotel.get("price")
            price_text = f"${round(float(price))}" if price not in (None, "None") else "n/a"
            print(f"{float(hotel.get('hotellist_rating') or 0):>5.2f}  {price_text:>6}  {hotel.get('name')}  [{hotel.get('hotel_id')}]")
        for warning in result["integrity_warnings"]:
            print(f"WARNING {warning['type']}: {warning['name']} [{warning['kept_id']}/{warning['other_id']}]", file=sys.stderr)
    elif command == "detail":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for item in result["items"][:limit]:
            print(f"{item.get('position', ''):>3}. {item.get('name')} — {item.get('url')}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--max-age", type=int, default=3600, help="cache lifetime in seconds; -1 disables cache reads")
    sub = parser.add_subparsers(dest="command", required=True)

    search_parser = sub.add_parser("search")
    search_parser.add_argument("place", nargs="?")
    search_parser.add_argument("--country", help="country name or two-letter code for geocoder disambiguation")
    search_parser.add_argument("--pick", type=int, help="choose a 1-based Photon locality candidate")
    search_parser.add_argument("--lat", type=float)
    search_parser.add_argument("--lng", type=float)
    search_parser.add_argument("--radius-km", type=float, default=10.0)
    search_parser.add_argument("--max-price", type=float)
    search_parser.add_argument("--min-rating", type=float)
    search_parser.add_argument("--newer-than", type=int)
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.add_argument("--json", action="store_true")

    detail_parser = sub.add_parser("detail")
    detail_parser.add_argument("hotel_id")
    detail_parser.add_argument("--json", action="store_true")

    city_parser = sub.add_parser("city")
    city_parser.add_argument("slug")
    city_parser.add_argument("--limit", type=int, default=15)
    city_parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "search":
            if (args.lat is None) != (args.lng is None):
                raise HotelistError("--lat and --lng must be provided together")
            result = search(
                place=args.place,
                country=args.country,
                pick=args.pick,
                lat=args.lat,
                lng=args.lng,
                radius_km=args.radius_km,
                max_price=args.max_price,
                min_rating=args.min_rating,
                newer_than=args.newer_than,
                limit=args.limit,
                max_age=args.max_age,
            )
            limit = args.limit
        elif args.command == "detail":
            result = detail(args.hotel_id, max_age=args.max_age)
            limit = 0
        else:
            result = city(args.slug, max_age=args.max_age)
            limit = args.limit
    except AmbiguousPlace as exc:
        payload = {"error": "ambiguous_place", "place": exc.place, "candidates": exc.candidates}
        print(json.dumps(payload, indent=2, ensure_ascii=False), file=sys.stderr)
        return 2
    except (HotelistError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    if getattr(args, "json", False):
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _print_human(args.command, result, limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
