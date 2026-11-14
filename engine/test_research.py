"""Tests for the optional AI answers about the curated NASA PSI records (research.py and /api/research/ask)."""
import json
import os
import unittest

import research
import server
from test_server import Base, FREELLM_KEY, completion

DATASET = research.load_dataset()
QUESTION = "What flame spread rate did Saffire II report for the 20 cm/s run?"


def reply(status="answered", answer="Saffire II run 2-5 reported a flame spread rate of 2.1 mm/s with 20 cm/s concurrent flow.", uses=("PSI-99:2-5",)):
    return json.dumps({"status": status, "answer": answer, "uses": list(uses)})


def check(text, question=QUESTION, ids=None):
    _, _, data = research.ask_request(DATASET, question, ids)
    return research.validate_answer(text, data, question, DATASET)


class Validation(unittest.TestCase):
    def test_a_grounded_answer_is_accepted(self):
        ans, notes = check(reply())
        self.assertEqual(notes, [])
        self.assertEqual(ans["uses"], ["PSI-99:2-5"])

    def test_dataset_is_the_curated_three(self):
        self.assertEqual(sorted(r["id"] for r in DATASET["records"]), ["PSI-25", "PSI-98", "PSI-99"])
        self.assertIn("PSI-99:2-5", research.valid_ids(DATASET))

    def test_numbers_must_come_from_the_records_or_the_question(self):
        ans, notes = check(reply(answer="Saffire II reported 7.3 mm/s."))
        self.assertIsNone(ans)
        self.assertEqual(notes, ["unsupported_number"])

    def test_claims_links_and_disclosure_are_rejected(self):
        for text, why in (("This burn rate is safe for a habitat.", "unsupported_claim"),
                          ("See https://psi.nasa.gov for more.", "citation_or_link"),
                          ("As an AI I can say the rate was 2.1 mm/s.", "implementation_disclosure")):
            ans, notes = check(reply(answer=text))
            self.assertIsNone(ans, text)
            self.assertEqual(notes, [why], text)

    def test_a_negated_claim_is_allowed(self):
        ans, _ = check(reply(status="cannot_answer", answer="The records are not a validation of any lunar habitat, and report no lunar-gravity rate.", uses=("PSI-99",)))
        self.assertIsNotNone(ans)

    def test_an_answer_must_cite_a_real_record(self):
        ans, notes = check(reply(uses=("PSI-77",)))
        self.assertIsNone(ans)
        self.assertEqual(notes, ["no_valid_references"])
        ans, _ = check(reply(status="cannot_answer", uses=()))
        self.assertIsNotNone(ans)

    def test_bad_shapes_are_rejected(self):
        for text in ("not json", json.dumps({"status": "maybe", "answer": "x", "uses": []}), json.dumps({"status": "answered", "answer": 5, "uses": []}),
                     reply(answer="x" * (research.MAX_ANSWER_CHARS + 1))):
            self.assertIsNone(check(text)[0])

    def test_request_sends_data_only_and_can_narrow_records(self):
        system, user, data = research.ask_request(DATASET, QUESTION, ["PSI-99", 7, None])
        self.assertEqual([r["id"] for r in data["records"]], ["PSI-99"])
        self.assertTrue(user.startswith("<data>") and user.endswith("</data>"))
        self.assertNotIn("sha256", user)
        self.assertTrue(all("raw" not in run for r in data["records"] for run in r["runs"]))
        _, _, all_data = research.ask_request(DATASET, QUESTION, ["nope"])
        self.assertEqual(len(all_data["records"]), 3)  # an unknown id falls back to every record

    def test_the_question_is_capped(self):
        _, _, data = research.ask_request(DATASET, "q" * 5000)
        self.assertEqual(len(data["question"]), research.MAX_QUESTION_CHARS)


class Route(Base):
    def setUp(self):
        super().setUp()
        os.environ["AI_PROVIDER"] = "freellmapi"
        os.environ["FREELLMAPI_API_KEY"] = FREELLM_KEY

    def ask(self, **body):
        return self.req("POST", "/api/research/ask", body=dict({"question": QUESTION}, **body))

    def test_an_answer_that_passes_the_checks_is_labelled_and_returned(self):
        self.responder = lambda req, timeout: completion(content=reply())
        code, body, _ = self.ask(ids=["PSI-99"])
        self.assertEqual(code, 200, body)
        self.assertEqual((body["mode"], body["uses"]), ("ai", ["PSI-99:2-5"]))
        self.assertIn("Not written or reviewed by a person", body["label"])
        sent = json.loads(self.calls[0][0].data)
        self.assertEqual(sent["messages"][0]["content"], research.ASK_SYSTEM)
        self.assertIn("PSI-99", sent["messages"][1]["content"])
        self.assertNotIn("PSI-25", sent["messages"][1]["content"])  # only the investigation on screen was sent

    def test_a_failing_check_withholds_the_answer(self):
        self.responder = lambda req, timeout: completion(content=reply(answer="It reached 9.9 mm/s."))
        code, body, _ = self.ask()
        self.assertEqual((code, body["mode"]), (200, "withheld"))
        self.assertNotIn("9.9", json.dumps(body))

    def test_citation_format_variants_resolve_to_real_ids(self):
        ids = research.valid_ids(DATASET)
        for text, want in (("PSI-99:2-5", "PSI-99:2-5"), ("PSI-99 row 2-5", "PSI-99:2-5"), ("PSI-99, run 2-5", "PSI-99:2-5"),
                           ("psi-99 sample 2-5", "PSI-99:2-5"), ("PSI-99", "PSI-99"), ("PSI-99:9-9", "PSI-99"), ("PSI-77", None), ("2-5", None), (5, None)):
            self.assertEqual(research.normalise_ref(text, ids), want, text)
        ans, notes = check(reply(uses=("PSI-99 row 2-5", "PSI-99:2-5")))
        self.assertEqual((notes, ans["uses"]), ([], ["PSI-99:2-5"]))  # variants of one run count once

    def test_a_withheld_reply_logs_only_the_reason_code(self):
        self.responder = lambda req, timeout: completion(content=reply(answer="It reached 9.9 mm/s."))
        self.ask()
        log = self.out.getvalue()
        self.assertIn("Research explanation withheld: unsupported_number", log)
        self.assertNotIn("9.9", log)

    def test_without_a_configured_service_it_says_so_and_calls_nothing(self):
        del os.environ["FREELLMAPI_API_KEY"]
        code, body, _ = self.ask()
        self.assertEqual((code, body["mode"], body["status"]), (200, "unavailable", "not_configured"))
        self.assertEqual(self.calls, [])

    def test_bad_requests_are_refused_before_any_network_call(self):
        for body in ({}, {"question": ""}, {"question": "   "}, {"question": 5}):
            code, _, _ = self.req("POST", "/api/research/ask", body=body)
            self.assertEqual(code, 400, body)
        self.assertEqual(self.calls, [])

    def test_service_failures_become_a_generic_message(self):
        def boom(req, timeout):
            raise OSError("down")
        self.responder = boom
        code, body, _ = self.ask()
        self.assertEqual((code, body["mode"]), (200, "unavailable"))
        self.assertNotIn(FREELLM_KEY, json.dumps(body))


if __name__ == "__main__":
    unittest.main(verbosity=2)
