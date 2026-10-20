import importlib.util
import io
import json
import unittest
import urllib.error
import urllib.parse
import urllib.request
import uuid
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "check_endpoints.py"
spec = importlib.util.spec_from_file_location("check_endpoints_cli", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {MODULE_PATH}")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class JsonTests(unittest.TestCase):
    def test_nested_list(self):
        data = {"data": {"navigation_bar": {"tabs": ["Home"]}}}
        self.assertTrue(checks.check_json(data, "data.navigation_bar.tabs", True))

    def test_empty_list_only_allowed_when_optional(self):
        self.assertTrue(checks.check_json({"data": []}, "data"))
        self.assertFalse(checks.check_json({"data": []}, "data", True))

    def test_missing_and_wrong_types(self):
        for data in (None, [], {}, {"data": None}, {"data": "[]"}, {"data": {}}):
            with self.subTest(data=data):
                self.assertFalse(checks.check_json(data, "data"))
                self.assertFalse(checks.check_json(data, "data.items"))
        self.assertFalse(checks.check_json({}, ""))


class BlockingTests(unittest.TestCase):
    def test_refusal_statuses_regardless_of_body(self):
        for status in (403, 429):
            self.assertTrue(checks.looks_blocked(status, "{}"))

    def test_html_challenges_case_insensitive(self):
        for marker in ("Just a moment", "Access to this page has been denied", "CAPTCHA"):
            for status in (200, 503):
                self.assertTrue(checks.looks_blocked(status, f"<html><title>{marker}</title></html>"))
        self.assertTrue(checks.looks_blocked(200, '<div class="g-recaptcha"></div>'))

    def test_normal_html_and_json_are_not_challenges(self):
        self.assertFalse(checks.looks_blocked(200, '<html><div data-testid="store-card"></div></html>'))
        self.assertFalse(checks.looks_blocked(200, '{"name":"captcha pizza"}'))
        self.assertFalse(checks.looks_blocked(500, "internal error"))

    def test_challenge_takes_precedence_over_marker(self):
        row = checks.check_response("glovo", "url", 200,
                                    '<html>Just a moment data-testid="store-card"</html>')
        self.assertEqual(row["outcome"], "BLOCKED")

    def test_captcha_script_on_a_real_page_is_not_a_block(self):
        page = '<html><script src="recaptcha.js"></script><a data-testid="store-card">Pizza</a></html>'
        self.assertEqual(checks.check_response("glovo", "url", 200, page)["outcome"], "OK")
        bare = '<html><div class="g-recaptcha"></div></html>'
        self.assertEqual(checks.check_response("glovo", "url", 200, bare)["outcome"], "BLOCKED")


class ResponseTests(unittest.TestCase):
    def test_documented_json_fields(self):
        for platform, (path, non_empty) in checks.JSON_CHECKS.items():
            data = [1] if non_empty else []
            for key in reversed(path.split(".")):
                data = {key: data}
            with self.subTest(platform=platform):
                self.assertEqual(checks.check_response(platform, "url", 200, json.dumps(data))["outcome"], "OK")
                self.assertEqual(checks.check_response(platform, "url", 200, "{}")["outcome"], "FAIL")
                self.assertEqual(checks.check_response(platform, "url", 200, "not JSON")["outcome"], "FAIL")

    def test_html_markers(self):
        for platform, marker in checks.HTML_CHECKS.items():
            self.assertEqual(checks.check_response(platform, "url", 200, marker)["outcome"], "OK")
            self.assertEqual(checks.check_response(platform, "url", 200, "<html></html>")["outcome"], "FAIL")

    def test_unexpected_http_status(self):
        for status in (301, 404, 500):
            self.assertEqual(checks.check_response("wolt", "url", status, '{"results":[1]}')["outcome"], "FAIL")


class FormattingTests(unittest.TestCase):
    def test_exact_line_and_date_header(self):
        row = checks.result("wolt", "https://example.test", 200, "OK", "results found")
        line = "wolt | https://example.test | 200 | OK | results found"
        self.assertEqual(checks.format_line(row), line)
        self.assertEqual(checks.format_output([row], "2026-10-20"),
                         "Endpoint drift check | 2026-10-20\n" + line)

    def test_no_status_and_untrusted_multiline_note(self):
        row = checks.result("efood", "url", None, "SKIPPED", "14 MB\nunsafe | text")
        self.assertEqual(checks.format_line(row), "efood | url | - | SKIPPED | 14 MB unsafe / text")

    def test_json_output(self):
        rows = [checks.result("wolt", "url", 200, "OK", "list found")]
        self.assertEqual(json.loads(checks.format_output(rows, "2026-10-20", True)),
                         {"date": "2026-10-20", "results": rows})


class ProbeTests(unittest.TestCase):
    def test_efood_never_requests(self):
        client = Mock()
        row = checks.probe("efood", client)
        client.request.assert_not_called()
        self.assertEqual(row["outcome"], "SKIPPED")
        self.assertIn("14 MB", row["note"])

    def test_uber_body_headers_and_only_location_cookie(self):
        client = Mock()
        client.request.return_value = (200, '{"data":[]}')
        self.assertEqual(checks.probe("uber-eats", client)["outcome"], "OK")
        url, body, headers = client.request.call_args.args
        self.assertEqual(url, checks.ENDPOINTS["uber-eats"])
        self.assertEqual(json.loads(body), {"userQuery": "pizza", "date": "", "startTime": 0,
                                          "endTime": 0, "vertical": "ALL"})
        self.assertEqual(headers["x-csrf-token"], "x")
        self.assertEqual(headers["Content-Type"], "application/json")
        name, value = headers["Cookie"].split("=", 1)
        self.assertEqual(name, "uev2.loc")
        location = json.loads(urllib.parse.unquote(value))
        self.assertEqual((location["latitude"], location["longitude"]), (51.508, -0.128))
        self.assertEqual(location["addressComponents"]["countryCode"], "GB")
        self.assertNotIn(";", headers["Cookie"])
        self.assertNotIn("{", value)

    def test_bolt_manifest_then_documented_query(self):
        client = Mock()
        client.request.side_effect = [(200, '{"version":"1.120.0"}'),
                                      (200, '{"data":{"navigation_bar":{"tabs":[1]}}}')]
        row = checks.probe("bolt-food", client)
        self.assertEqual(row["outcome"], "OK")
        self.assertEqual(client.request.call_count, 2)
        self.assertEqual(client.request.call_args_list[0].args, (checks.BOLT_MANIFEST,))
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(row["endpoint"]).query)
        device_id = query.pop("deviceId")[0]
        self.assertEqual(uuid.UUID(device_id).version, 4)
        self.assertEqual(query, {"delivery_lat": ["52.230"], "delivery_lng": ["21.012"],
                                 "version": ["FW.1.120.0"], "language": ["en-US"],
                                 "deviceType": ["web"], "device_name": ["web"],
                                 "device_os_version": ["web"]})

    def test_bolt_stops_on_manifest_problems(self):
        for response, outcome in (((403, ""), "BLOCKED"), ((429, ""), "BLOCKED"),
                                  ((200, "<html>captcha</html>"), "BLOCKED"),
                                  ((500, ""), "FAIL"), ((200, "{}"), "FAIL"),
                                  ((200, "[]"), "FAIL"), ((200, "bad JSON"), "FAIL")):
            client = Mock()
            client.request.return_value = response
            self.assertEqual(checks.probe("bolt-food", client)["outcome"], outcome)
            client.request.assert_called_once()

    def test_network_failure_no_retry(self):
        client = Mock()
        client.request.side_effect = urllib.error.URLError("offline")
        row = checks.probe("wolt", client)
        self.assertEqual(row["outcome"], "FAIL")
        self.assertIsNone(row["status"])
        client.request.assert_called_once()

    def test_delivery_hero_header(self):
        client = Mock()
        client.request.return_value = (200, '{"data":{"items":[]}}')
        self.assertEqual(checks.probe("delivery-hero", client)["outcome"], "OK")
        self.assertEqual(client.request.call_args.args[2], {"x-disco-client-id": "web"})

    def test_main_selection_deduplicates_and_exit_codes(self):
        for outcome, exit_code in (("OK", 0), ("FAIL", 1), ("BLOCKED", 1), ("SKIPPED", 0)):
            row = checks.result("wolt", "url", 200, outcome, "note")
            with patch.object(checks, "probe", return_value=row) as probe, redirect_stdout(io.StringIO()) as output:
                self.assertEqual(checks.main(["--platform", "wolt", "wolt", "--json"]), exit_code)
                probe.assert_called_once()
                self.assertEqual(len(json.loads(output.getvalue())["results"]), 1)


class ClientTests(unittest.TestCase):
    def test_user_agent_timeout_sleep_and_no_cookie_storage(self):
        response = Mock(status=200)
        response.read.return_value = b"{}"
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value = response
        with patch.object(checks.urllib.request, "build_opener", return_value=opener), patch.object(checks.time, "sleep") as sleep:
            client = checks.Client()
            self.assertEqual(client.request("https://example.test"), (200, "{}"))
            sleep.assert_not_called()
            client.request("https://example.test")
            sleep.assert_called_once_with(1.5)
        for call in opener.open.call_args_list:
            self.assertEqual(call.kwargs, {"timeout": 30})
            self.assertEqual(call.args[0].get_header("User-agent"), checks.USER_AGENT)
            self.assertIsNone(call.args[0].get_header("Cookie"))

    def test_http_error_body_is_checked_without_retry(self):
        error = urllib.error.HTTPError("https://example.test", 429, "limited", {}, io.BytesIO(b"blocked"))
        client = checks.Client()
        client.opener = Mock()
        client.opener.open.side_effect = error
        self.assertEqual(client.request("https://example.test"), (429, "blocked"))
        client.opener.open.assert_called_once()

    def test_only_same_site_redirects_are_followed(self):
        req = urllib.request.Request("https://deliveroo.co.uk/restaurants/london/soho?geohash=gcpvhd")
        handler = checks.SameSiteRedirect()
        same = handler.redirect_request(req, None, 302, "Found", {}, "https://deliveroo.co.uk/restaurants/london/fitzrovia")
        self.assertEqual(same.full_url, "https://deliveroo.co.uk/restaurants/london/fitzrovia")
        self.assertIsNone(handler.redirect_request(req, None, 302, "Found", {}, "https://elsewhere.test/"))
        self.assertIsNone(handler.redirect_request(req, None, 302, "Found", {}, "http://deliveroo.co.uk/restaurants/london"))


if __name__ == "__main__":
    unittest.main()
