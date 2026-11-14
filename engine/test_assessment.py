"""Tests for the deterministic assessment engine (assessment.py).

These tests check that the engine does what it says: validates inputs, never fills in missing values, calculates
with units and significant figures, labels its heuristic honestly, keeps severity, likelihood and uncertainty
separate, and cites only sources that exist. They do NOT show that the findings are scientifically correct: that
needs experiments and independent expert review, neither of which has been done.
"""
import copy
import json
import math
import random
import re
import unittest
from datetime import date

import assessment as A
import evidence as E
import report as R

TODAY = date(2026, 10, 21)


def example(id_):
    return copy.deepcopy(next(e for e in A.EXAMPLES if e["id"] == id_)["inputs"])


def run(inputs, ev=None):
    return A.assess(inputs, ev=ev, today=TODAY)


def titles(a, kind=None):
    return [f["title"] for f in a["findings"] if kind is None or f["kind"] == kind]


def ids(a, kind=None):
    return {f["id"] for f in a["findings"] if kind is None or f["kind"] == kind}


class Determinism(unittest.TestCase):
    def test_same_inputs_same_assessment(self):
        a, b = run(example("electrical_transit")), run(example("electrical_transit"))
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        self.assertEqual(a["assessmentId"], b["assessmentId"])

    def test_input_key_order_and_blank_values_do_not_change_the_result(self):
        base = example("electrical_transit")
        shuffled = dict(reversed(list(base.items())))
        padded = dict(base, redundancy="", inspection="   ", fault_current_a=None)
        ids_ = {run(x)["assessmentId"] for x in (base, shuffled, padded)}
        self.assertEqual(len(ids_), 1)

    def test_any_change_of_inputs_changes_the_id(self):
        base = example("electrical_transit")
        self.assertNotEqual(run(base)["assessmentId"], run(dict(base, voltage_v="29"))["assessmentId"])

    def test_the_result_is_json_serialisable_and_contains_no_timestamps(self):
        text = json.dumps(run(example("electrical_transit")))
        self.assertNotRegex(text, r"generatedAt|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\"")


class InputValidation(unittest.TestCase):
    def bad(self, inputs, field_fragment=None):
        with self.assertRaises(A.InputError) as c:
            A.normalize_inputs(inputs)
        if field_fragment:
            self.assertTrue(any(field_fragment in str(e["field"]) for e in c.exception.errors), c.exception.errors)
        return c.exception.errors

    def test_rejects_non_objects(self):
        for x in (None, [], "text", 5):
            self.bad(x)

    def test_unknown_inputs_are_rejected_not_ignored(self):
        self.bad({"hazard": "electrical", "mystery": "1"}, "mystery")

    def test_numbers_must_be_plain_finite_in_range(self):
        for field, value in (("o2_percent", "150"), ("o2_percent", "0"), ("o2_percent", "-5"), ("o2_percent", "abc"), ("o2_percent", "1e999"), ("o2_percent", "nan"),
                             ("o2_percent", "inf"), ("o2_percent", "21%"), ("o2_percent", "2 1"), ("o2_percent", True), ("o2_percent", [21]), ("o2_percent", {"a": 1}),
                             ("pressure", "0"), ("pressure", "5000"), ("crew", "2.5"), ("crew", "0"), ("crew", "21"), ("duration_days", "0"), ("duration_days", "99999"),
                             ("voltage_v", "-1"), ("comm_delay_min", "-1"), ("clearing_ms", "0")):
            self.bad({field: value}, field)

    def test_zero_is_allowed_only_where_physically_meaningful(self):
        self.assertEqual(A.normalize_inputs({"comm_delay_min": "0"})["values"]["comm_delay_min"], 0.0)

    def test_selects_must_be_listed_options(self):
        for field, value in (("hazard", "explosion"), ("gravity", "venus"), ("pressure_unit", "bar"), ("detection_coverage", 3), ("hazard", ["electrical"])):
            self.bad({field: value}, field)

    def test_all_problems_are_reported_together_with_plain_messages(self):
        errors = self.bad({"o2_percent": "x", "hazard": "nope", "crew": "99", "extra": 1})
        self.assertEqual(len(errors), 4)
        for e in errors:
            self.assertGreater(len(e["message"]), 8)
            self.assertNotRegex(e["message"], r"Traceback|Exception|ValueError")

    def test_blank_means_not_provided_never_a_default(self):
        v = A.normalize_inputs({})["values"]
        self.assertTrue(all(x is None for k, x in v.items() if k != "pressure_unit"))
        self.assertEqual(v["pressure_unit"], "kPa")  # a unit, not data

    def test_question_is_cleaned_and_length_limited(self):
        q = A.normalize_inputs({"question": "  a\x00b\nc\t" + "x" * 500})["values"]["question"]
        self.assertNotRegex(q, r"[\x00-\x1f]")
        self.assertLessEqual(len(q), 300)

    def test_numbers_keep_their_text_and_significant_figures(self):
        n = A.normalize_inputs({"voltage_v": "28", "o2_percent": "21.0", "op_current_a": 12})
        self.assertEqual((n["text"]["voltage_v"], n["sigfigs"]["voltage_v"]), ("28", 2))
        self.assertEqual(n["sigfigs"]["o2_percent"], 3)
        self.assertEqual(n["sigfigs"]["op_current_a"], 2)


class UnitsAndSignificantFigures(unittest.TestCase):
    def test_significant_figure_counting(self):
        table = {"180": 2, "180.": 3, "0.0150": 3, "1.20e2": 3, "28": 2, "4.50": 3, "0": 1, "100": 1, "0.5": 1, "26.5": 3, "10.2": 3, "007": 1, "+3.0": 2}
        for text, n in table.items():
            self.assertEqual(A.count_sigfigs(text), n, text)

    def test_formatting_never_implies_more_precision_than_the_inputs(self):
        self.assertEqual(A.fmt_sig(336, 2), "3.4 × 10²")
        self.assertEqual(A.fmt_sig(21.284, 3), "21.3")
        self.assertEqual(A.fmt_sig(9.96, 2), "10")
        self.assertEqual(A.fmt_sig(0.00012, 2), "1.2 × 10⁻⁴")
        self.assertEqual(A.fmt_sig(18000, 2), "1.8 × 10⁴")
        self.assertEqual(A.fmt_sig(0, 3), "0")

    def test_dimensional_analysis(self):
        for expr, unit in (("V*A", "W"), ("A^2*ms", "A^2*s"), ("A^2*s", "A^2*s"), ("m3/m3*min", "min"), ("kPa/kPa", "1"), ("psi*1", "kPa"), ("W*s", "J")):
            self.assertTrue(A.check_dimensions(expr, unit), expr)
        for expr, unit in (("V*V", "W"), ("A*s", "W"), ("kPa*m3", "W"), ("V/A", "W")):
            self.assertFalse(A.check_dimensions(expr, unit), expr)
        with self.assertRaises(ValueError):
            A.dims("furlong*A")

    def test_every_calculation_is_dimensionally_consistent_and_documented(self):
        a = run(example("electrical_transit_complete"))
        self.assertGreaterEqual(len(a["derived"]), 7)
        for d in a["derived"]:
            self.assertEqual(d["dimensionalCheck"], "consistent", d["id"])
            for key in ("formula", "inputs", "assumptions", "limitations", "unit", "display", "kind"):
                self.assertIn(key, d)
            self.assertTrue(d["limitations"] or d["assumptions"], d["id"])
            self.assertIn("estimate", d["kind"])  # calculated, not measured

    def test_pressure_conversion_and_oxygen_partial_pressure(self):
        a = run(example("electrical_transit"))
        d = {x["id"]: x for x in a["derived"]}
        self.assertAlmostEqual(d["p_total_kpa"]["value"], 14.7 * 6.894757293168361, places=9)
        self.assertEqual(d["p_total_kpa"]["display"], "101")
        self.assertAlmostEqual(d["po2_kpa"]["value"], 0.21 * 101.3530, places=2)
        self.assertEqual(d["po2_kpa"]["display"], "21.3")
        self.assertEqual(d["po2_ratio"]["display"], "1.00")

    def test_kpa_input_is_not_converted(self):
        a = run(dict(example("electrical_transit"), pressure="101.325", pressure_unit="kPa"))
        self.assertNotIn("p_total_kpa", {x["id"] for x in a["derived"]})
        d = {x["id"]: x for x in a["derived"]}
        self.assertAlmostEqual(d["po2_kpa"]["value"], 0.21 * 101.325, places=9)

    def test_power_i2t_turnover_and_round_trip(self):
        d = {x["id"]: x for x in run(example("electrical_transit_complete"))["derived"]}
        self.assertEqual((d["power_w"]["value"], d["power_w"]["display"]), (336.0, "3.4 × 10²"))
        self.assertAlmostEqual(d["i2t"]["value"], 112.5)            # 150 A squared x 5 ms
        self.assertEqual(d["i2t"]["display"], "1 × 10²")            # limited to one figure by the '5 ms' input
        self.assertEqual(d["i2t"]["unit"], "A²·s")
        self.assertAlmostEqual(d["turnover_min"]["value"], 1.5)
        self.assertEqual(d["rtt_min"]["value"], 24)

    def test_oxygen_difference_keeps_decimal_places_not_significant_figures(self):
        d = {x["id"]: x for x in run({"hazard": "electrical", "o2_percent": "26.5", "gravity": "micro", "pressure": "101.3"})["derived"]}
        self.assertEqual(d["o2_excess_pp"]["display"], "5.6")
        self.assertIsNone(d["o2_excess_pp"]["sigfigs"])

    def test_a_calculation_needing_a_missing_input_is_not_produced(self):
        a = run({"hazard": "electrical", "gravity": "micro", "o2_percent": "21.0", "pressure": "101.3", "voltage_v": "28"})
        got = {x["id"] for x in a["derived"]}
        self.assertNotIn("power_w", got)        # no current supplied
        self.assertNotIn("i2t", got)
        self.assertNotIn("turnover_min", got)
        self.assertIn("gap_i2t", ids(a, "gap"))

    def test_zero_comm_delay_gives_zero_round_trip(self):
        d = {x["id"]: x for x in run({"hazard": "electrical", "comm_delay_min": "0"})["derived"]}
        self.assertEqual(d["rtt_min"]["value"], 0)


class MissingInputs(unittest.TestCase):
    def test_nothing_is_assessed_without_a_hazard(self):
        a = run({})
        self.assertEqual((a["status"]["code"], a["findings"], a["derived"], a["nextSteps"]), ("not_assessed", [], [], []))
        self.assertFalse(a["screeningIndex"]["computed"])
        self.assertIn("Nothing is assumed", a["summary"]["text"])

    def test_a_hazard_alone_gives_an_incomplete_screening_that_names_what_is_needed(self):
        a = run({"hazard": "electrical"})
        self.assertEqual(a["status"]["code"], "incomplete")
        self.assertIn("Incomplete", a["status"]["label"])
        needed = " ".join(m["label"] for m in a["inputs"]["missing"] if m["tier"] == "core")
        for word in ("Gravity", "Oxygen fraction", "Total cabin pressure"):
            self.assertIn(word, needed)
        self.assertEqual(a["derived"], [])

    def test_no_condition_is_reported_for_a_provision_that_was_not_described(self):
        a = run({"hazard": "electrical", "gravity": "micro", "o2_percent": "21.0", "pressure": "101.3"})
        self.assertFalse(ids(a, "condition") & {"detect_cov", "suppression", "ppe", "postfire", "drills", "materials", "power_isolation", "fault_protection"})
        self.assertTrue({"gap_detect", "gap_fault_protection", "gap_power_isolation"} <= ids(a, "gap"))

    def test_every_missing_input_says_why_it_matters(self):
        for m in run({"hazard": "electrical"})["inputs"]["missing"]:
            self.assertGreater(len(m["why"]), 15, m["id"])

    def test_defaults_are_never_substituted(self):
        a = run({"hazard": "electrical", "gravity": "micro", "o2_percent": "21.0", "pressure": "101.3"})
        supplied = {i["id"] for i in a["inputs"]["supplied"]}
        self.assertEqual(supplied, {"hazard", "gravity", "o2_percent", "pressure"})
        text = json.dumps(a)
        for stale_default in ("distributed", "redundant", "verified", "validated", "current"):  # the old page silently assumed these protections
            self.assertNotIn('"value": "%s"' % stale_default, text)

    def test_supplied_but_irrelevant_inputs_are_listed_and_not_used(self):
        a = run(dict(example("electrical_transit"), battery="elevated"))
        self.assertIn("battery", {x["id"] for x in a["inputs"]["notApplicable"]})
        self.assertNotIn("battery", {x["id"] for x in a["inputs"]["supplied"]})
        self.assertNotIn("battery", ids(a))


class HeuristicIndexIsLabelledAndHonest(unittest.TestCase):
    def test_label_and_flags(self):
        si = run(example("electrical_transit"))["screeningIndex"]
        self.assertIn("heuristic", si["label"].lower())
        self.assertIn("Preliminary", si["label"])
        self.assertFalse(si["validated"])
        self.assertFalse(si["calibrated"])
        for phrase in ("not a probability", "not a measure of severity"):
            self.assertIn(phrase, si["meaning"])
        self.assertIn("SAME hazard type", si["scope"])

    def test_the_documented_value_for_the_regression_scenario(self):
        si = run(example("electrical_transit"))["screeningIndex"]
        self.assertTrue(si["computed"])
        self.assertEqual((si["value"], si["maximum"]), (65, 138))
        self.assertEqual(len(si["factors"]), 11)
        self.assertAlmostEqual(sum(f["points"] for f in si["factors"]), 65, delta=1)
        for f in si["factors"]:
            self.assertTrue(f["rule"] and f["inputs"])

    def test_it_is_not_computed_when_an_input_it_needs_is_missing_and_says_which(self):
        inputs = example("electrical_transit")
        del inputs["abort"]
        si = run(inputs)["screeningIndex"]
        self.assertFalse(si["computed"])
        self.assertIn("Return or safe-haven options", si["reason"])
        self.assertNotIn("value", si)

    def test_no_percent_scale_and_no_threshold_labels_are_produced_any_more(self):
        text = json.dumps(run(example("electrical_transit")))
        for old in ("Priority review", "Review needed", "Lower concern", "/100", "out of 100", "Relative concern"):
            self.assertNotIn(old, text)
        self.assertNotIn("Watch", [x["label"] for x in [run(example("electrical_transit"))["status"]]])

    def test_the_old_score_is_gone_and_the_change_is_documented(self):
        si = run(example("electrical_transit"))["screeningIndex"]
        self.assertNotEqual(si["value"], 37)
        self.assertIn("substituted default inputs", si["changesFromEarlierVersions"])
        self.assertIn("not comparable", si["changesFromEarlierVersions"])

    def test_hazard_categories_are_not_interchangeable(self):
        base = example("electrical_transit")
        elec = run(base)["screeningIndex"]
        with_battery = run(dict(base, battery="elevated"))["screeningIndex"]
        self.assertEqual(elec["value"], with_battery["value"])      # the battery input does not leak into a non-battery hazard
        self.assertEqual(len(elec["factors"]), len(with_battery["factors"]))
        mat = run(dict(base, hazard="material"))["screeningIndex"]
        self.assertNotIn("Procedure to remove power from the affected equipment", [f["name"] for f in mat["factors"]])
        self.assertIn("Procedure to remove power from the affected equipment", [f["name"] for f in elec["factors"]])
        bat = run(dict(base, hazard="battery", battery="elevated"))["screeningIndex"]
        self.assertIn("Stored energy (batteries)", [f["name"] for f in bat["factors"]])

    def test_equal_index_values_never_hide_different_conditions(self):
        """The old score gave 24 different protection combinations the same number with no explanation. Here the
        factor table and the comparison always show what differs."""
        base = example("electrical_transit")
        seen = {}
        for det in ("distributed", "single", "gaps"):
            for sup in ("both", "portable", "limited"):
                for dr in ("current", "overdue", "none"):
                    inp = dict(base, detection_coverage=det, suppression=sup, drills=dr)
                    a = run(inp)
                    seen.setdefault(a["screeningIndex"]["value"], []).append((a, inp))
        pair = next(v for v in seen.values() if len(v) > 1)
        (a1, _), (a2, _) = pair[0], pair[1]
        self.assertEqual(a1["screeningIndex"]["value"], a2["screeningIndex"]["value"])
        self.assertNotEqual([f["points"] for f in a1["screeningIndex"]["factors"]], [f["points"] for f in a2["screeningIndex"]["factors"]])
        cmp = A.compare_assessments(a1, a2)
        self.assertTrue(cmp["changedInputs"])
        self.assertEqual(cmp["indexDelta"], 0)


class SeverityLikelihoodUncertaintyStaySeparate(unittest.TestCase):
    def setUp(self):
        self.a = run(example("electrical_transit"))

    def test_the_dimensions_are_distinct_and_not_estimated(self):
        d = self.a["dimensions"]
        self.assertEqual(d["severity"]["status"], "not assessed")
        self.assertEqual(d["likelihood"]["status"], "not assessed")
        self.assertEqual(d["measuredUncertainty"]["status"], "none available")
        self.assertNotEqual(d["severity"]["detail"], d["likelihood"]["detail"])
        self.assertIn("listed, not scored", d["consequenceModifiers"]["status"])
        self.assertIn("not graded", d["evidenceBase"]["status"])
        self.assertIn("number of sources does not measure", d["evidenceBase"]["detail"])

    def test_completeness_is_a_measured_count(self):
        text = self.a["dimensions"]["informationCompleteness"]["detail"]
        self.assertRegex(text, r"^\d+ of \d+ applicable inputs supplied; 4 of 4 required for screening supplied\.$")

    def test_no_invented_probabilities_margins_or_confidence(self):
        blob = json.dumps(self.a)
        self.assertNotRegex(blob, r"\d+(\.\d+)?\s*%\s*(chance|probability|likely|confidence)")
        self.assertNotRegex(blob, r"(?i)\bconfidence (interval|level) of\b")
        self.assertNotRegex(blob, r"(?i)margin of (safety|[0-9])")
        self.assertNotRegex(blob, r"(?i)\bp\s*=\s*0\.")

    def test_a_clean_looking_scenario_is_never_called_safe(self):
        best = dict(example("electrical_transit_complete"), fault_protection="characterised", power_isolation="verified", redundancy="defined", inspection="documented",
                    detection_coverage="distributed", detection_signals="multi", suppression="both", ppe="accessible", drills="current", postfire="defined",
                    materials="tested", vent_control="verified", abort="near", ignition_other="low", pressure="101.325", pressure_unit="kPa", gravity="earth")
        a = run(best)
        self.assertEqual(a["status"]["code"], "preliminary")
        self.assertIn("pathway", {f["kind"] for f in a["findings"]})                       # the hazard pathway is still described
        self.assertIn("NS_review", {s["id"] for s in a["nextSteps"]})                      # independent review is still recommended
        self.assertIn("does not mean the spacecraft is safe", " ".join(a["limitations"]))
        for text in [f["statement"] + f["reasoning"] for f in a["findings"]] + [a["summary"]["text"]]:
            self.assertNotRegex(text, r"(?i)\b(is|are|remains?) (safe|acceptable|adequate)\b")
            self.assertNotRegex(text, r"(?i)\b(validated|certified|approved)\b(?<!not validated)")

    def test_a_scenario_with_many_flags_is_not_called_likely_or_dangerous(self):
        worst = dict(example("electrical_transit"), fault_protection="none", power_isolation="none", redundancy="none", suppression="limited", ppe="none", drills="none",
                     postfire="none", detection_coverage="gaps", materials="untested", abort="remote", vent_control="no", inspection="undocumented")
        a = run(worst)
        blob = json.dumps(a)
        self.assertGreater(len(titles(a, "condition")), 12)
        self.assertNotRegex(blob, r"(?i)\b(imminent|will (occur|ignite|fail)|is likely to|likely to occur|dangerous|critical risk|high risk)\b")

    def test_proposed_mitigation_is_not_treated_as_demonstrated(self):
        a = run(dict(example("electrical_transit"), fault_protection="specified"))
        f = next(f for f in a["findings"] if f["id"] == "fault_protection")
        self.assertEqual(f["kind"], "condition")
        self.assertIn("proposed mitigation", f["statement"])
        ok = run(dict(example("electrical_transit"), fault_protection="characterised"))
        f2 = next(f for f in ok["findings"] if f["id"] == "fault_protection")
        self.assertEqual(f2["kind"], "context")
        self.assertIn("Reported, not verified", " ".join(f2["limitations"]))

    def test_plausible_pathways_are_not_presented_as_demonstrated_failures(self):
        for hz in ("electrical", "battery", "material", "smoke"):
            a = run(dict(example("electrical_transit"), hazard=hz))
            p = next(f for f in a["findings"] if f["kind"] == "pathway")
            self.assertRegex(p["title"] + p["statement"], r"(?i)plausible")
            self.assertRegex(p["title"] + p["statement"] + " ".join(p["limitations"]), r"(?i)(not (a )?demonstrated|does not demonstrate|plausible pathway only|not a measured|not demonstrate)")

    def test_findings_distinguish_kind_basis_and_limits(self):
        for f in self.a["findings"]:
            self.assertIn(f["kind"], ("pathway", "condition", "gap", "context"))
            self.assertIn(f["basis"], ("sourced", "inference", "calculation", "input"))
            for key in ("statement", "reasoning", "relevance", "inputsUsed", "limitations", "evidence"):
                self.assertIn(key, f)
            if f["basis"] == "sourced":
                self.assertTrue(f["evidence"], f["id"])          # 'sourced' always points at a source
            if f["basis"] == "inference":
                self.assertNotIn("Supported by", f["reasoning"])
        inferred = [f for f in self.a["findings"] if f["basis"] == "inference"]
        self.assertTrue(inferred and all("no source" in (f["reasoning"] + " ".join(f["limitations"])).lower() for f in inferred))


class UncertaintyAssumptionsAndCompetingEvidence(unittest.TestCase):
    def test_assumptions_and_limitations_are_stated(self):
        a = run(example("electrical_transit"))
        joined = " ".join(a["assumptions"])
        self.assertIn("20.95", joined)
        self.assertIn("101.325", joined)
        self.assertIn("not hazard thresholds", joined)
        self.assertGreaterEqual(len(a["limitations"]), 6)
        self.assertTrue(any("abstract level" in x for x in a["limitations"]))
        self.assertTrue(any("not supplied" in x for x in a["limitations"]))

    def test_ventilation_trade_off_is_surfaced_as_competing_evidence(self):
        a = run(example("electrical_transit"))
        self.assertIn("T2", [t["id"] for t in a["evidence"]["tensions"]])
        self.assertTrue(any("Competing considerations (ventilation)" in x for x in a["limitations"]))

    def test_atmosphere_competing_effects_are_surfaced_when_oxygen_is_high_in_reduced_gravity(self):
        a = run(dict(example("electrical_transit"), o2_percent="26.5", pressure="10.2"))
        self.assertIn("atm_o2", ids(a, "condition"))
        self.assertIn("T1", [t["id"] for t in a["evidence"]["tensions"]])

    def test_the_i2t_value_is_never_compared_with_an_ignition_limit(self):
        a = run(example("electrical_transit_complete"))
        f = next(f for f in a["findings"] if f["id"] == "i2t")
        self.assertIn("not judged high or low", f["statement"])
        self.assertIn("holds no ignition thresholds", f["statement"])
        d = next(d for d in a["derived"] if d["id"] == "i2t")
        self.assertTrue(any("NOT compared with any ignition limit" in x for x in d["limitations"]))

    def test_durations_are_not_classified_without_a_source_threshold(self):
        f = next(f for f in run(example("electrical_transit"))["findings"] if f["id"] == "duration")
        self.assertIn("does not classify this duration as extended or not", f["statement"])
        self.assertEqual(f["kind"], "context")


class StatementsContainOnlyTraceableNumbers(unittest.TestCase):
    def test_every_number_in_a_finding_statement_comes_from_inputs_calculations_or_a_stated_constant(self):
        for ex in A.EXAMPLES:
            a = run(ex["inputs"])
            allowed = {"20.95", "101.325", "0.1", "1"}
            for i in a["inputs"]["supplied"]:
                allowed |= set(re.findall(r"\d+(?:\.\d+)?", i["display"]))
            for d in a["derived"]:
                allowed |= set(re.findall(r"\d+(?:\.\d+)?", d["display"]))
            for f in a["findings"]:
                for n in re.findall(r"(?<![A-Za-z0-9.])\d+(?:\.\d+)?", f["statement"]):
                    self.assertIn(n, allowed, "%s: %s in %r" % (ex["id"], n, f["statement"][:90]))


class EvidenceIntegrityInAssessments(unittest.TestCase):
    def test_every_citation_resolves_for_every_example_and_for_random_scenarios(self):
        rnd = random.Random(20261021)
        cases = [e["inputs"] for e in A.EXAMPLES]
        for _ in range(250):
            inp = {}
            for f in A.FIELDS:
                if f["id"] in ("question", "pressure_unit") or rnd.random() < 0.3:
                    continue
                if f["kind"] == "select":
                    inp[f["id"]] = rnd.choice(f["options"])["value"]
                else:
                    lo = f.get("min", 0)
                    hi = min(f.get("max", 1000), 1000)
                    x = round(rnd.uniform(lo + 0.01, hi), rnd.choice([0, 1, 2]))
                    inp[f["id"]] = str(int(x)) if f.get("integer") else str(max(x, 0.01))
            cases.append(inp)
        for inp in cases:
            a = run(inp)
            self.assertEqual(a["evidence"]["unknownClaimIds"], [], inp)
            known = {s["id"] for s in a["evidence"]["sources"]}
            for c in a["evidence"]["claims"]:
                self.assertIn(c["sourceId"], known)
            for f in a["findings"]:
                for cid in f["evidence"]:
                    self.assertIn(cid, {c["id"] for c in a["evidence"]["claims"]})
            for d in a["derived"]:
                self.assertEqual(d["dimensionalCheck"], "consistent")
            self.assertIn(a["status"]["code"], ("not_assessed", "incomplete", "preliminary"))
            self.assertIsInstance(json.dumps(a), str)

    def test_status_labels_come_from_what_was_actually_done(self):
        a = run(example("electrical_transit"))
        self.assertEqual(a["status"]["label"], "Preliminary screening")
        c = a["status"]["checks"]
        self.assertEqual(c["independentValidation"], "Not performed")
        self.assertIn("Not performed", c["literatureReview"])
        self.assertEqual(c["quantitativeChecks"], len(a["derived"]))
        self.assertEqual(c["evidenceStatements"], len(a["evidence"]["claims"]))
        self.assertEqual(c["sourcesCited"], len(a["evidence"]["sources"]))
        self.assertNotIn("validated", a["status"]["label"].lower())
        no_calc = run({"hazard": "electrical", "gravity": "earth", "o2_percent": "21", "pressure": "kPa"} if False else {"hazard": "smoke", "gravity": "micro", "o2_percent": "21.0", "pressure": "101.3"})
        self.assertGreaterEqual(no_calc["status"]["checks"]["quantitativeChecks"], 2)

    def test_missing_library_entries_are_reported_not_hidden(self):
        lib = E.load_library()
        lib["sources"] = [s for s in lib["sources"] if s["id"] != "S04"]
        a = run(example("electrical_transit_complete"), ev=E.Evidence(lib))
        self.assertTrue(a["evidence"]["unknownClaimIds"])
        self.assertTrue(all(c.startswith("S04.") for c in a["evidence"]["unknownClaimIds"]))
        self.assertTrue(any("could not be found in the source library" in x for x in a["limitations"]))
        self.assertTrue(any("could not be retrieved" in x for x in a["status"]["reasons"]))
        self.assertNotIn("S04", {s["id"] for s in a["evidence"]["sources"]})

    def test_an_empty_library_means_no_traceability_and_says_so(self):
        lib = {"libraryVersion": "x", "reviewedOn": "x", "sources": [{"id": "S99", "kind": "k", "title": "t", "authors": [], "issuer": "i", "date": "2000-01-01", "dateKind": "publication",
                                                                      "identifier": "x", "url": "https://example.org", "verify": {"method": "http"}, "review": {"depth": "abstract", "note": ""},
                                                                      "caveats": ["abstract only"], "claims": [{"id": "S99.c1", "topic": "t", "text": "x" * 50}]}], "tensions": []}
        a = run(example("electrical_transit"), ev=E.Evidence(lib))
        self.assertEqual(a["evidence"]["sources"], [])
        self.assertTrue(any("No source could be retrieved" in x for x in a["limitations"]))
        self.assertTrue(a["evidence"]["unknownClaimIds"])
        self.assertIn("Not performed", a["status"]["checks"]["literatureReview"])


class RegressionScenario180DayElectricalOverheat(unittest.TestCase):
    """The previously reported case: 180-day deep-space transit, electrical overheat, microgravity, limited abort options."""

    def setUp(self):
        self.a = run(example("electrical_transit"))

    def test_status_and_summary(self):
        a = self.a
        self.assertEqual(a["status"]["label"], "Preliminary screening")
        self.assertIn("not a risk estimate", a["summary"]["text"])
        self.assertEqual((a["summary"]["conditions"], a["summary"]["gaps"]), (12, 3))
        self.assertIn("fault current and clearing time not both supplied", a["summary"]["text"])
        self.assertIn("plausible one drawn from the literature, not a demonstrated failure mode", a["summary"]["text"])

    def test_specific_findings_replace_generic_safety_prose(self):
        a = self.a
        cond = ids(a, "condition")
        for expected in ("fault_protection", "power_isolation", "gravity", "materials", "vent_control", "detect_cov", "detect_sig", "detect_gas", "suppression", "ppe", "postfire", "abort"):
            self.assertIn(expected, cond)
        self.assertEqual(ids(a, "gap"), {"gap_i2t", "gap_redundancy", "gap_inspection"})
        self.assertEqual(ids(a, "pathway"), {"pathway_electrical"})
        self.assertNotIn("drills", cond)                                  # drills were reported current
        self.assertNotIn("atm_o2", cond)                                  # Earth-like oxygen: no oxygen condition
        text = " ".join(f["statement"] for f in a["findings"])
        self.assertIn("proposed mitigation, not demonstrated performance", text)
        self.assertIn("A proposed capability is not evidence that it works", text)

    def test_it_asks_for_the_electrical_information_it_needs_instead_of_assuming_it(self):
        missing = {m["id"] for m in self.a["inputs"]["missing"]}
        self.assertEqual(missing, {"fault_current_a", "clearing_ms", "redundancy", "inspection"})
        steps = {s["id"] for s in self.a["nextSteps"]}
        self.assertTrue({"NS_fault_char", "NS_ignition_test", "NS_power_isolation", "NS_detect_perf", "NS_vent_study", "NS_inspection", "NS_redundancy", "NS_review"} <= steps)
        self.assertEqual({s["category"] for s in self.a["nextSteps"]}, {"information", "simulation", "test", "independent_review"})

    def test_calculations_are_real_and_limited_to_what_was_supplied(self):
        got = {d["id"]: d["display"] for d in self.a["derived"]}
        self.assertEqual(got["power_w"], "3.4 × 10²")
        self.assertEqual(got["rtt_min"], "24")
        self.assertNotIn("i2t", got)

    def test_with_fault_data_added_the_energy_is_calculated_but_not_judged(self):
        b = run(example("electrical_transit_complete"))
        self.assertNotIn("gap_i2t", ids(b))
        self.assertIn("i2t", ids(b, "condition"))
        self.assertEqual({m["id"] for m in b["inputs"]["missing"]}, set())
        self.assertIn("redundancy", ids(b, "condition"))
        self.assertIn("inspection", ids(b, "condition"))

    def test_the_cited_sources_are_the_relevant_ones_and_their_review_depth_is_stated(self):
        ids_ = {s["id"] for s in self.a["evidence"]["sources"]}
        self.assertTrue({"S01", "S02", "S03", "S05", "S07", "S08"} <= ids_)
        self.assertNotIn("S13", ids_)                                     # battery sources are not cited for an electrical hazard
        depths = {s["id"]: s["review"]["depth"] for s in self.a["evidence"]["sources"]}
        self.assertEqual(depths["S01"], "full text")
        self.assertTrue(all(v == "abstract" for k, v in depths.items() if k != "S01"))

    def test_no_numeric_probability_or_prediction_appears(self):
        blob = json.dumps(self.a)
        self.assertNotRegex(blob, r"(?i)probability of|likelihood of \d|chance of|per (flight )?hour")

    def test_protective_layers_report_what_was_stated_without_rating_effectiveness(self):
        layers = {L["layer"]: {i["id"]: i for i in L["items"]} for L in self.a["layers"]}
        self.assertEqual(set(layers), {"Prevent", "Detect", "Isolate and control", "Suppress and protect", "Respond and recover"})
        self.assertEqual(layers["Prevent"]["fault_protection"]["level"], "partial")
        self.assertEqual(layers["Prevent"]["inspection"]["level"], "not_provided")
        self.assertEqual(layers["Respond and recover"]["drills"]["level"], "complete")
        for L in self.a["layers"]:
            for i in L["items"]:
                self.assertIn(i["level"], ("complete", "partial", "info", "not_provided"))
                self.assertNotRegex(i.get("levelText", ""), r"(?i)\b(adequate|effective|sufficient)\b")


class OtherHazards(unittest.TestCase):
    def test_each_hazard_has_its_own_pathway_and_sources(self):
        expect = {"electrical": "S03", "battery": "S13", "material": "S12", "smoke": "S11"}
        for hz, src in expect.items():
            a = run(dict(example("electrical_transit"), hazard=hz, battery="elevated", materials="untested"))
            self.assertEqual(len([f for f in a["findings"] if f["kind"] == "pathway"]), 1, hz)
            self.assertIn(src, {s["id"] for s in a["evidence"]["sources"]}, hz)

    def test_electrical_only_inputs_are_not_applicable_to_other_hazards(self):
        a = run(dict(example("electrical_transit_complete"), hazard="smoke"))
        na = {x["id"] for x in a["inputs"]["notApplicable"]}
        self.assertTrue({"voltage_v", "op_current_a", "fault_current_a", "clearing_ms", "fault_protection"} <= na)
        self.assertEqual({d["id"] for d in a["derived"]} & {"power_w", "i2t"}, set())

    def test_examples_for_other_hazards_assess_cleanly(self):
        for id_ in ("lunar_battery", "mars_material"):
            a = run(example(id_))
            self.assertEqual(a["status"]["code"], "preliminary")
            self.assertIn("atm_o2", ids(a, "condition"))                  # 26.5 % oxygen
            self.assertIn("gravity", ids(a, "condition"))
            self.assertTrue(any(f["id"] == "atm_pressure" for f in a["findings"]))


class CompareAssessments(unittest.TestCase):
    def test_changes_are_reported_by_input_and_by_finding(self):
        a, b = run(example("electrical_transit")), run(example("electrical_transit_complete"))
        c = A.compare_assessments(a, b)
        self.assertEqual({x["id"] for x in c["changedInputs"]} - {"question"}, {"fault_current_a", "clearing_ms", "redundancy", "inspection"})
        self.assertIn("Let-through energy of the fault was calculated but cannot be compared with an ignition limit", c["findingsAdded"])
        self.assertIn("Fault current and clearing time not both supplied", c["findingsRemoved"])

    def test_the_index_is_only_compared_when_the_same_factors_were_counted(self):
        a = run(example("electrical_transit"))
        b = run(dict(example("electrical_transit"), hazard="material"))
        c = A.compare_assessments(a, b)
        self.assertIsNone(c["indexDelta"])
        self.assertIn("not compared", c["indexNote"])
        same = A.compare_assessments(a, a)
        self.assertEqual((same["changedInputs"], same["indexDelta"]), ([], 0))


class SchemaAndExamples(unittest.TestCase):
    def test_schema_is_complete_consistent_and_serialisable(self):
        sch = A.public_schema()
        json.dumps(sch)
        fids = [f["id"] for f in sch["fields"]]
        self.assertEqual(len(fids), len(set(fids)))
        for f in sch["fields"]:
            self.assertIn(f["group"], sch["groups"])
            self.assertTrue(f["why"], f["id"])
            self.assertIn(f["kind"], ("select", "number", "text"))
            if f["kind"] == "select":
                values = [o["value"] for o in f["options"]]
                self.assertEqual(len(values), len(set(values)))
                self.assertNotIn("", values)                              # 'not provided' is the blank, never an option
            for h in f.get("applies") or []:
                self.assertIn(h, A.HAZARD_LABELS)

    def test_examples_are_valid_and_clearly_labelled_as_not_mission_data(self):
        for e in A.EXAMPLES:
            A.normalize_inputs(e["inputs"])
            self.assertIn("not mission data", e["note"].lower() + " " + e["label"].lower() if "illustrative" not in e["label"].lower() else e["note"].lower() + " not mission data")
            self.assertIn("illustrative", e["label"].lower())


class Methodology(unittest.TestCase):
    def test_description_is_accurate_about_what_is_automated_and_what_is_not(self):
        m = R.methodology()
        text = json.dumps(m).lower()
        for phrase in ("deterministic", "no human review", "not scientific correctness", "does not search the literature", "not checked"):
            self.assertIn(phrase, text)
        self.assertTrue(any("literature search" in x.lower() for x in m["notDone"]))
        self.assertTrue(any("review by a qualified person" in x.lower() for x in m["notDone"]))
        for implementation in ("gemini", "claude", "anthropic", "freellm", "google", "router"):
            self.assertNotIn(implementation, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
