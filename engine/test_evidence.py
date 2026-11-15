"""Tests for the curated source library and citation handling (evidence.py, evidence/sources.json).

These check structure and honesty of the records (every cited id exists, sources are https NASA documents, abstract-only
sources say so, duplicates and unknown ids are handled, verification statuses are truthful). They cannot show that a
statement in the library is a correct reading of its source; that was done by a person reading the source once and is
recorded per source in its review.depth field.
"""
import copy
import io
import json
import unittest
import urllib.error
from datetime import date
from urllib.parse import urlparse

import evidence as E

TODAY = date(2026, 10, 21)


def lib():
    return copy.deepcopy(E.load_library())


class FakeResponse:
    def __init__(self, body=b"", headers=None):
        self._b, self.headers = body, headers or {}

    def read(self, n=-1):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def ntrs_opener(title_for):
    def opener(req, timeout=None):
        sid = req.full_url.rsplit("/", 1)[-1]
        t = title_for(sid)
        if isinstance(t, Exception):
            raise t
        return FakeResponse(json.dumps({"id": sid, "title": t}).encode())
    return opener


class ShippedLibrary(unittest.TestCase):
    def setUp(self):
        self.lib = E.load_library()

    def test_it_is_structurally_valid(self):
        self.assertEqual(E.validate_library(self.lib), [])

    def test_shape_and_size(self):
        self.assertEqual(len(self.lib["sources"]), 14)
        self.assertGreaterEqual(sum(len(s["claims"]) for s in self.lib["sources"]), 30)

    def test_every_url_is_https_and_nasa_hosted(self):
        for s in self.lib["sources"]:
            host = urlparse(s["url"]).hostname or ""
            self.assertEqual(urlparse(s["url"]).scheme, "https", s["id"])
            self.assertTrue(host == "nasa.gov" or host.endswith(".nasa.gov"), (s["id"], host))

    def test_abstract_only_sources_say_so_and_only_one_is_marked_full_text(self):
        depths = {s["id"]: s["review"]["depth"] for s in self.lib["sources"]}
        self.assertEqual([k for k, v in depths.items() if v == "full text"], ["S01"])
        for s in self.lib["sources"]:
            if s["review"]["depth"] == "abstract":
                self.assertTrue(any("abstract" in c.lower() for c in s["caveats"]), s["id"])

    def test_claims_are_specific_statements_not_slogans(self):
        for s in self.lib["sources"]:
            for c in s["claims"]:
                self.assertGreaterEqual(len(c["text"]), 40, c["id"])
                self.assertNotRegex(c["text"], r"(?i)\b(proves?|guarantees?|always safe|completely safe|validated)\b", c["id"])

    def test_no_claim_states_a_numerical_probability_or_margin(self):
        for s in self.lib["sources"]:
            for c in s["claims"]:
                self.assertNotRegex(c["text"], r"(?i)\d\s*%\s*(chance|probability)|probability of \d|margin of \d", c["id"])

    def test_dates_are_real_and_in_the_past(self):
        for s in self.lib["sources"]:
            y, m, d = map(int, s["date"].split("-"))
            self.assertLessEqual(date(y, m, d), TODAY, s["id"])

    def test_tensions_reference_real_claims_and_have_notes(self):
        ids = {c["id"] for s in self.lib["sources"] for c in s["claims"]}
        self.assertGreaterEqual(len(self.lib["tensions"]), 2)
        for t in self.lib["tensions"]:
            self.assertTrue(set(t["claims"]) <= ids)
            self.assertGreater(len(t["note"]), 40)

    def test_old_unsupported_citations_are_not_reintroduced(self):
        """The earlier page cited two NTRS records for statements they do not support (one has no battery content, one has no abstract)."""
        text = json.dumps(self.lib)
        for nid in ("20210021318",):
            self.assertNotIn(nid, text)
        s06 = next(s for s in self.lib["sources"] if s["id"] == "S06")
        self.assertNotRegex(" ".join(c["text"] for c in s06["claims"]).lower(), r"batter")

    def test_s12_is_flagged_as_possibly_superseded(self):
        s12 = next(s for s in self.lib["sources"] if s["id"] == "S12")
        self.assertRegex(" ".join(s12["caveats"]).lower(), r"supersed|older|revision|current")


class LibraryValidationRejectsBadRecords(unittest.TestCase):
    def mutate(self, fn):
        L = lib()
        fn(L)
        return E.validate_library(L)

    def has(self, problems, fragment):
        self.assertTrue(any(fragment in p for p in problems), problems)

    def test_missing_field(self):
        self.has(self.mutate(lambda L: L["sources"][0].pop("caveats")), "missing field caveats")

    def test_bad_ids(self):
        self.has(self.mutate(lambda L: L["sources"][0].update(id="X1")), "id must look like")

    def test_duplicate_source_id(self):
        def f(L):
            L["sources"][1]["id"] = L["sources"][0]["id"]
        self.has(self.mutate(f), "duplicate source id")

    def test_duplicate_url(self):
        def f(L):
            L["sources"][1]["url"] = L["sources"][0]["url"]
        self.has(self.mutate(f), "duplicate url")

    def test_non_https_url(self):
        self.has(self.mutate(lambda L: L["sources"][0].update(url="http://ntrs.nasa.gov/x")), "url must be https")

    def test_bad_date(self):
        self.has(self.mutate(lambda L: L["sources"][0].update(date="2023")), "date must be")

    def test_abstract_only_without_caveat(self):
        def f(L):
            s = L["sources"][2]
            s["review"]["depth"] = "abstract"
            s["caveats"] = ["Something else."]
        self.has(self.mutate(f), "must say so in their caveats")

    def test_claim_id_must_belong_to_its_source(self):
        def f(L):
            L["sources"][0]["claims"][0]["id"] = "S09.c1"
        self.has(self.mutate(f), "doesn't belong")

    def test_duplicate_claim_id(self):
        def f(L):
            L["sources"][0]["claims"][1]["id"] = L["sources"][0]["claims"][0]["id"]
        self.has(self.mutate(f), "duplicate claim id")

    def test_claim_too_short_or_without_topic(self):
        def f(L):
            L["sources"][0]["claims"][0]["text"] = "Fire is bad."
            L["sources"][0]["claims"][1]["topic"] = ""
        p = self.mutate(f)
        self.has(p, "too short")
        self.has(p, "no topic")

    def test_unknown_verification_method(self):
        self.has(self.mutate(lambda L: L["sources"][0]["verify"].update(method="trust-me")), "unknown verify.method")

    def test_tension_with_unknown_claim_or_single_claim_or_no_note(self):
        def f(L):
            L["tensions"][0]["claims"] = ["S99.c9"]
            L["tensions"][0]["note"] = ""
        p = self.mutate(f)
        self.has(p, "unknown claim")
        self.has(p, "at least two")
        self.has(p, "no explanatory note")

    def test_empty_or_wrong_type(self):
        for bad in (None, {}, {"sources": []}, {"sources": "x"}, []):
            self.assertEqual(E.validate_library(bad), ["library has no sources"])


class Citing(unittest.TestCase):
    def setUp(self):
        self.ev = E.Evidence()

    def test_duplicates_are_collapsed_and_order_of_first_use_is_kept(self):
        r = self.ev.cite(["S04.c2", "S01.c7", "S04.c2", "S01.c7", "S01.c3"], TODAY)
        self.assertEqual([c["id"] for c in r["claims"]], ["S04.c2", "S01.c7", "S01.c3"])
        self.assertEqual([s["id"] for s in r["sources"]], ["S04", "S01"])
        self.assertEqual(r["unknown"], [])

    def test_unknown_ids_are_reported_and_never_invented(self):
        r = self.ev.cite(["S01.c3", "S99.c1", "S01.c999", "nonsense"], TODAY)
        self.assertEqual(r["unknown"], ["S99.c1", "S01.c999", "nonsense"])
        self.assertEqual([s["id"] for s in r["sources"]], ["S01"])

    def test_public_source_lists_only_the_cited_claims_and_adds_age_and_verification(self):
        s = self.ev.cite(["S01.c3"], TODAY)["sources"][0]
        self.assertEqual([c["id"] for c in s["claims"]], ["S01.c3"])
        self.assertEqual(s["review"]["depth"], "full text")
        self.assertEqual(s["ageYears"], 2)
        self.assertIsNone(s["olderThanYears"])
        self.assertEqual(s["verification"]["status"], "not_checked")

    def test_old_sources_are_labelled_by_age_not_judged(self):
        s = self.ev.cite(["S02.c2"], TODAY)["sources"][0]
        self.assertGreaterEqual(s["ageYears"], E.STALE_YEARS)
        self.assertEqual(s["olderThanYears"], E.STALE_YEARS)
        self.assertNotIn("outdated", json.dumps(s).lower())

    def test_conflicting_evidence_surfaces_only_when_both_sides_are_cited(self):
        t = self.ev.tensions[0]
        both = self.ev.cite(t["claims"], TODAY)
        self.assertIn(t["id"], [x["id"] for x in both["tensions"]])
        one = self.ev.cite(t["claims"][:1], TODAY)
        self.assertNotIn(t["id"], [x["id"] for x in one["tensions"]])

    def test_age_years(self):
        self.assertEqual(E.age_years("2016-10-21", TODAY), 10)
        self.assertEqual(E.age_years("2016-10-22", TODAY), 9)
        self.assertEqual(E.age_years("2030-01-01", TODAY), 0)
        self.assertIsNone(E.age_years("not a date", TODAY))
        self.assertIsNone(E.age_years(None, TODAY))

    def test_partial_library_retrieval(self):
        L = lib()
        L["sources"] = [s for s in L["sources"] if s["id"] in ("S01", "S02")]
        L["tensions"] = [t for t in L["tensions"] if all(c.startswith(("S01", "S02")) for c in t["claims"])]
        ev = E.Evidence(L)
        r = ev.cite(["S01.c3", "S04.c2", "S02.c2"], TODAY)
        self.assertEqual(r["unknown"], ["S04.c2"])
        self.assertEqual({s["id"] for s in r["sources"]}, {"S01", "S02"})


class LiveVerification(unittest.TestCase):
    """Uses fake network openers only. These tests say nothing about the real NTRS service."""

    def setUp(self):
        self.ev = E.Evidence()
        self.titles = {s["verify"]["ntrsId"]: s["verify"]["expectedTitle"] for s in self.ev.lib["sources"] if s["verify"]["method"] == "ntrs"}

    def test_all_verified_when_titles_match(self):
        summary = self.ev.verify_all(ntrs_opener(lambda sid: self.titles.get(sid, "")))
        self.assertEqual((summary["checked"], summary["problems"]), (14, 0))
        self.assertEqual(summary["verified"], 14)
        self.assertEqual(self.ev.verification_for("S01")["status"], "verified")
        self.assertIsNotNone(summary["lastChecked"])

    def test_title_mismatch_is_reported_not_hidden(self):
        first = next(s for s in self.ev.lib["sources"] if s["verify"]["method"] == "ntrs")
        bad = first["verify"]["ntrsId"]
        summary = self.ev.verify_all(ntrs_opener(lambda sid: "A different title" if sid == bad else self.titles.get(sid, "")))
        self.assertEqual(self.ev.verification_for(first["id"])["status"], "title_mismatch")
        self.assertGreaterEqual(summary["problems"], 1)
        self.assertIn("differs", self.ev.verification_for(first["id"])["detail"])

    def test_title_comparison_ignores_case_and_whitespace_only(self):
        first = next(s for s in self.ev.lib["sources"] if s["verify"]["method"] == "ntrs")
        r = E.verify_one(first, ntrs_opener(lambda sid: "  " + first["verify"]["expectedTitle"].upper().replace(" ", "  ") + " "))
        self.assertEqual(r["status"], "verified")
        r = E.verify_one(first, ntrs_opener(lambda sid: first["verify"]["expectedTitle"] + " (Revised)"))
        self.assertEqual(r["status"], "title_mismatch")

    def test_failures_become_unreachable_without_leaking_details(self):
        first = next(s for s in self.ev.lib["sources"] if s["verify"]["method"] == "ntrs")
        errors = [urllib.error.HTTPError("https://ntrs.nasa.gov/x", 503, "secret upstream text", {}, io.BytesIO(b"body")), urllib.error.URLError("dns failure at 10.1.2.3"),
                  TimeoutError("timed out"), ValueError("bad json")]
        for e in errors:
            r = E.verify_one(first, ntrs_opener(lambda sid, e=e: e))
            self.assertEqual(r["status"], "unreachable")
            self.assertNotRegex(r["detail"], r"10\.1\.2\.3|secret|body|dns|Traceback")
        r = E.verify_one(first, ntrs_opener(lambda sid: errors[0]))
        self.assertIn("HTTP 503", r["detail"])

    def test_malformed_record_is_not_verified(self):
        first = next(s for s in self.ev.lib["sources"] if s["verify"]["method"] == "ntrs")
        for body in (b"[]", b"null", b"not json", b'{"title": 5}'):
            r = E.verify_one(first, lambda req, timeout=None, b=body: FakeResponse(b))
            self.assertNotEqual(r["status"], "verified", body)

    def test_http_method_checks_content_type(self):
        s = {"id": "S50", "url": "https://www.nasa.gov/x.pdf", "verify": {"method": "http", "expectedContentType": "application/pdf"}}
        ok = E.verify_one(s, lambda req, timeout=None: FakeResponse(headers={"Content-Type": "application/pdf; charset=binary"}))
        bad = E.verify_one(s, lambda req, timeout=None: FakeResponse(headers={"Content-Type": "text/html"}))
        self.assertEqual((ok["status"], bad["status"]), ("verified", "title_mismatch"))
        self.assertIn("not re-read", ok["detail"])

    def test_verification_statement_does_not_claim_the_content_was_checked(self):
        r = E.verify_one(next(s for s in self.ev.lib["sources"] if s["verify"]["method"] == "ntrs"), ntrs_opener(lambda sid: self.titles[sid]))
        self.assertNotRegex(r["detail"].lower(), r"content (is|was) (correct|verified)|accurate")

    def test_nothing_is_marked_verified_before_a_check_runs(self):
        for s in E.Evidence().all_sources(TODAY):
            self.assertEqual(s["verification"]["status"], "not_checked")


if __name__ == "__main__":
    unittest.main(verbosity=2)
