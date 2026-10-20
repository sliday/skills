#!/usr/bin/env python3
"""Read-only drift checks for documented delivery-app endpoints.

Examples:
  python3 check_endpoints.py
  python3 check_endpoints.py --platform wolt uber-eats --json

Requests are sequential, with a 1.5 s gap and a 30 s timeout. No retries,
cross-site redirects, login, or cookie storage are used. Same-site redirects
are followed because Deliveroo sends the listing to the right area that way.
External text is data only.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
)
BOLT_BASE = "https://deliveryuser.live.boltsvc.net/deliveryClient/public"
BOLT_MANIFEST = "https://food.bolt.eu/manifest.json"
ENDPOINTS = {
    "wolt": "https://consumer-api.wolt.com/v1/cities",
    "uber-eats": "https://www.ubereats.com/api/getSearchSuggestionsV1?localeCode=gb",
    "glovo": "https://glovoapp.com/en/es/madrid/categories/food_1",
    "bolt-food": BOLT_BASE + "/getNavigationBar",
    "delivery-hero": (
        "https://disco.deliveryhero.io/listing/api/v1/pandora/vendors"
        "?latitude=48.208&longitude=16.374&country=at&language_id=1"
        "&vertical=restaurants&limit=1&offset=0&opening_type=delivery"
    ),
    "just-eat-takeaway": (
        "https://rest.api.eu-central-1.production.jet-external.com"
        "/discovery/pl/restaurants/enriched/bypostcode/00-024"
    ),
    "deliveroo": "https://deliveroo.co.uk/restaurants/london/soho?geohash=gcpvhd",
    "efood": "https://api.e-food.gr/api/v1/restaurants/",
}
JSON_CHECKS = {
    "wolt": ("results", True),
    "uber-eats": ("data", False),
    "bolt-food": ("data.navigation_bar.tabs", True),
    "delivery-hero": ("data.items", False),
    "just-eat-takeaway": ("restaurants", True),
}
HTML_CHECKS = {"glovo": 'data-testid="store-card"', "deliveroo": 'id="__NEXT_DATA__"'}


def check_json(data: Any, path: str, non_empty: bool = False) -> bool:
    """Check a dotted dictionary path for a list, optionally non-empty."""
    if not path:
        return False
    value = data
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return False
        value = value[key]
    return isinstance(value, list) and (not non_empty or bool(value))


STRONG_CHALLENGE = ("just a moment", "access to this page has been denied")


def looks_blocked(status: int | None, body: str) -> bool:
    """Recognize refusal statuses and HTML challenge pages without retrying."""
    if status in (403, 429):
        return True
    text = body.lower()
    html = re.search(r"<\s*(?:!doctype\s+html|html\b|head\b|body\b|title\b|script\b|div\b)", text)
    return bool(html) and any(marker in text for marker in (*STRONG_CHALLENGE, "captcha"))


def is_strong_challenge(body: str) -> bool:
    """Challenge pages that never carry real content, unlike pages that only load a captcha script."""
    text = body.lower()
    return any(marker in text for marker in STRONG_CHALLENGE)


def uber_cookie() -> str:
    """Use only the documented anonymous London location, rounded to 3 decimals."""
    location = {
        "address": {"address1": "London", "address2": "London", "aptOrSuite": "",
                    "eaterFormattedAddress": "London", "subtitle": "London",
                    "title": "London", "uuid": ""},
        "latitude": 51.508, "longitude": -0.128,
        "reference": "", "referenceType": "google_places", "type": "google_places",
        "addressComponents": {"city": "London", "countryCode": "GB",
                              "firstLevelSubdivisionCode": "", "postalCode": ""},
        "categories": [], "originType": "user_autocomplete",
        "source": "manual_auto_complete", "userState": "Unknown",
    }
    return "uev2.loc=" + urllib.parse.quote(json.dumps(location, separators=(",", ":")), safe="")


class SameSiteRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new, old = urllib.parse.urlsplit(newurl), urllib.parse.urlsplit(req.full_url)
        if new.scheme != "https" or new.netloc != old.netloc:
            return None  # no cross-site hops and no downgrade to plain HTTP
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Client:
    def __init__(self) -> None:
        self.opener = urllib.request.build_opener(SameSiteRedirect())
        self.requested = False

    def request(self, url: str, body: bytes | None = None,
                headers: dict[str, str] | None = None) -> tuple[int, str]:
        if self.requested:
            time.sleep(1.5)
        self.requested = True
        request = urllib.request.Request(url, data=body, headers={
            "User-Agent": USER_AGENT, **(headers or {}),
        })
        try:
            with self.opener.open(request, timeout=30) as response:
                return response.status, response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            with exc:
                return exc.code, exc.read().decode("utf-8", errors="replace")


def result(platform: str, endpoint: str, status: int | None,
           outcome: str, note: str) -> dict[str, Any]:
    return dict(platform=platform, endpoint=endpoint, status=status, outcome=outcome, note=note)


def check_response(platform: str, endpoint: str, status: int, body: str) -> dict[str, Any]:
    blocked = result(platform, endpoint, status, "BLOCKED", "refusal or HTML challenge; no retry")
    if status in (403, 429) or (looks_blocked(status, body) and is_strong_challenge(body)):
        return blocked
    if not 200 <= status < 300:
        return result(platform, endpoint, status, "FAIL", "unexpected HTTP status; no retry")
    if platform in HTML_CHECKS and HTML_CHECKS[platform] not in body and looks_blocked(status, body):
        return blocked
    if platform in HTML_CHECKS:
        marker = HTML_CHECKS[platform]
        ok = marker in body
        note = f'{marker}: {"present" if ok else "missing"}'
    else:
        path, non_empty = JSON_CHECKS[platform]
        try:
            data = json.loads(body)
        except ValueError:
            return result(platform, endpoint, status, "FAIL", "response is not valid JSON")
        ok = check_json(data, path, non_empty)
        expected = "non-empty list" if non_empty else "list"
        note = f'{path}: {expected} {"found" if ok else "missing or wrong type"}'
    return result(platform, endpoint, status, "OK" if ok else "FAIL", note)


def probe(platform: str, client: Client) -> dict[str, Any]:
    endpoint = ENDPOINTS[platform]
    if platform == "efood":
        return result(platform, endpoint, None, "SKIPPED", "only endpoint returns 14 MB")
    status = None
    try:
        if platform == "bolt-food":
            endpoint = BOLT_MANIFEST
            status, body = client.request(endpoint)
            if looks_blocked(status, body):
                return result(platform, endpoint, status, "BLOCKED", "manifest refused or challenged; no retry")
            if not 200 <= status < 300:
                return result(platform, endpoint, status, "FAIL", "manifest HTTP failure; no retry")
            manifest = json.loads(body)
            version = manifest.get("version") if isinstance(manifest, dict) else None
            if not isinstance(version, str) or not version.strip():
                return result(platform, endpoint, status, "FAIL", "manifest version missing or wrong type")
            endpoint = ENDPOINTS[platform] + "?" + urllib.parse.urlencode({
                "delivery_lat": "52.230", "delivery_lng": "21.012",
                "version": "FW." + version, "language": "en-US", "deviceId": str(uuid.uuid4()),
                "deviceType": "web", "device_name": "web", "device_os_version": "web",
            })
        headers = {}
        body_bytes = None
        if platform == "uber-eats":
            headers = {"Content-Type": "application/json", "x-csrf-token": "x", "Cookie": uber_cookie()}
            body_bytes = json.dumps({"userQuery": "pizza", "date": "", "startTime": 0,
                                     "endTime": 0, "vertical": "ALL"}).encode("utf-8")
        elif platform == "delivery-hero":
            headers = {"x-disco-client-id": "web"}
        status = None
        status, body = client.request(endpoint, body_bytes, headers)
        return check_response(platform, endpoint, status, body)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        return result(platform, endpoint, status, "FAIL", f"{type(exc).__name__}: {exc}")


def format_line(row: dict[str, Any]) -> str:
    def cell(value: Any) -> str:
        return " ".join(str(value).replace("|", "/").split())
    return " | ".join(cell(value) for value in (
        row["platform"], row["endpoint"], row["status"] if row["status"] is not None else "-",
        row["outcome"], row["note"],
    ))


def format_output(rows: list[dict[str, Any]], today: str, as_json: bool = False) -> str:
    if as_json:
        return json.dumps({"date": today, "results": rows}, ensure_ascii=False, indent=2)
    return "\n".join([f"Endpoint drift check | {today}", *(format_line(row) for row in rows)])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--platform", nargs="+", action="extend", choices=list(ENDPOINTS))
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    args = parser.parse_args(argv)
    platforms = list(dict.fromkeys(args.platform or ENDPOINTS))
    client = Client()
    rows = [probe(platform, client) for platform in platforms]
    print(format_output(rows, date.today().isoformat(), args.json))
    return 0 if all(row["outcome"] in ("OK", "SKIPPED") for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
