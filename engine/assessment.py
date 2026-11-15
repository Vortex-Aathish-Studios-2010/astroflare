"""Astroflare deterministic assessment engine.

Pure code: no network, no AI, no randomness. Given the same inputs it always returns the same assessment.

What it does
  1. validates inputs (types, ranges, units) and records which ones were NOT supplied;
  2. runs dimension-checked calculations on supplied numbers, keeping significant figures;
  3. applies a fixed set of review rules to the supplied inputs; each rule's wording is tied to specific statements
     in the evidence library (evidence.py) or is labelled as inference;
  4. computes a heuristic "screening index" only when every input it needs was supplied;
  5. reports what is known, inferred and missing, and the follow-up work that would reduce uncertainty.

What it does NOT do
  It does not model combustion, fire growth, smoke transport or toxicology. It estimates no probability, frequency,
  severity, confidence interval or margin. It has not been validated against experiments or reviewed by a qualified
  safety authority, and its output must not be used as a safety determination.
"""
import hashlib
import json
import math
import re
from datetime import date

import evidence as evidence_lib

ENGINE_VERSION = "2026.10.21-2"  # -2: input basis recorded and flagged; unchanged inputs/rules/calculations
INDEX_LABEL = "Preliminary screening index (heuristic)"

# Reference values (physical constants/definitions used for comparisons; not hazard thresholds).
SEA_LEVEL_KPA = 101.325          # one standard atmosphere, exact by definition
AIR_O2_PERCENT = 20.95           # dry air, percent by volume (commonly quoted value)
PSIA_TO_KPA = 6.894757293168361  # pounds-force per square inch -> kilopascal
# Tolerances used only to decide whether two numbers are "the same" when comparing with the reference.
O2_EQUAL_TOL_PP = 0.1            # percentage points
PRESSURE_EQUAL_TOL = 0.01        # fraction of the reference pressure


class InputError(Exception):
    def __init__(self, errors):
        super().__init__("invalid inputs")
        self.errors = errors


# =====================================================================================================
# Field schema (the single source of truth: the page builds its form from this)
# =====================================================================================================

def _opts(*pairs):
    return [{"value": v, "label": l} for v, l in pairs]


H_ALL = None
FIELDS = [
    # ---- Scenario
    dict(id="question", label="Research question (optional)", group="Scenario", kind="text", maxlen=300, tier="detail",
         help="Shown with the results. Astroflare screens a fixed set of conditions; it cannot answer questions about probability or acceptability.",
         why="Without a stated question the default screening question is used."),
    dict(id="hazard", label="Hazard under investigation", group="Scenario", kind="select", tier="core", options=_opts(
        ("electrical", "Electrical overheating or arc"), ("battery", "Battery thermal event"),
        ("material", "Cabin material ignition"), ("smoke", "Persistent smoke or combustion products")),
        help="A what-if hazard pathway, not a prediction that it will occur.", why="The applicable rules and inputs depend on the hazard."),
    dict(id="habitat", label="Habitat or vehicle", group="Scenario", kind="select", tier="detail", options=_opts(
        ("transit", "Deep-space transit vehicle"), ("lunar", "Lunar surface habitat"), ("mars", "Mars surface habitat"),
        ("orbital", "Orbital habitat"), ("crewvehicle", "Crew ascent/descent vehicle")), why="Context for the report."),
    dict(id="phase", label="Mission phase", group="Scenario", kind="select", tier="detail", options=_opts(
        ("transit", "Transit / cruise"), ("surface", "Surface operations"), ("dormant", "Dormant / uncrewed interval"),
        ("airlock", "Airlock / spacewalk support")), why="Whether a crew is present to respond changes what can be assumed."),
    # ---- Environment
    dict(id="gravity", label="Gravity", group="Environment", kind="select", tier="core", options=_opts(
        ("micro", "Microgravity"), ("lunar", "Lunar (about 0.16 g)"), ("mars", "Martian (about 0.38 g)"), ("earth", "Earth-like (1 g)")),
        why="Gravity changes flame and smoke behaviour, and the data that apply."),
    dict(id="o2_percent", label="Oxygen fraction", group="Environment", kind="number", unit="% by volume", tier="core", min=0, max=100, exclusive_min=True,
         help="Percent by volume of the cabin atmosphere.", why="Oxygen content strongly affects material flammability; it is also needed to compute oxygen partial pressure."),
    dict(id="pressure", label="Total cabin pressure", group="Environment", kind="number", units=["kPa", "psia"], tier="core", min=0, max=1000, exclusive_min=True,
         why="Needed for oxygen partial pressure and to decide which test data apply."),
    dict(id="pressure_unit", label="Pressure unit", group="Environment", kind="select", tier="detail", default="kPa", options=_opts(("kPa", "kPa"), ("psia", "psia")),
         why="Unit for the pressure value."),
    dict(id="volume_m3", label="Volume of the affected compartment", group="Environment", kind="number", unit="m³", tier="quant", min=0, max=100000, exclusive_min=True,
         why="With the ventilation flow it gives the air turnover time scale."),
    dict(id="vent_flow_m3_min", label="Ventilation flow through the compartment", group="Environment", kind="number", unit="m³/min", tier="quant", min=0, max=100000, exclusive_min=True,
         why="With the compartment volume it gives the air turnover time scale."),
    dict(id="vent_control", label="Ability to stop ventilation to the affected compartment", group="Environment", kind="select", tier="detail", options=_opts(
        ("verified", "Can be stopped; verified"), ("unverified", "Can be stopped; not verified"), ("no", "Cannot be stopped independently")),
        why="Airflow can supply a fire with air and spread smoke, but detectors rely on airflow; the trade-off depends on this."),
    # ---- Mission constraints
    dict(id="duration_days", label="Mission duration", group="Mission constraints", kind="number", unit="days", tier="detail", min=0, max=3650, exclusive_min=True,
         why="Context; the cited literature lists extended duration among factors beyond past experience but gives no threshold."),
    dict(id="crew", label="Crew size", group="Mission constraints", kind="number", unit="persons", tier="detail", min=1, max=20, integer=True,
         why="Context for response capacity and exposure."),
    dict(id="abort", label="Return or safe-haven options", group="Mission constraints", kind="select", tier="detail", options=_opts(
        ("near", "Quick return or safe haven available"), ("limited", "Few alternatives"), ("remote", "No quick return / far from resupply")),
        why="Limits how much of the response can rely on outside help."),
    dict(id="comm_delay_min", label="One-way communication delay to ground", group="Mission constraints", kind="number", unit="minutes", tier="quant", min=0, max=1000,
         why="Sets the shortest possible time for a ground reply."),
    # ---- Electrical system
    dict(id="equip_type", label="Equipment type", group="Electrical system", kind="select", tier="detail", applies=["electrical"], options=_opts(
        ("distribution", "Power distribution / wiring harness"), ("conversion", "Power conversion / avionics electronics"),
        ("motor", "Motors, fans or pumps"), ("payload", "Payload or experiment electronics"), ("other", "Other")),
        why="Different equipment has different fault and heating behaviour."),
    dict(id="voltage_v", label="Operating voltage", group="Electrical system", kind="number", unit="V", tier="quant", applies=["electrical"], min=0, max=1000000, exclusive_min=True,
         why="With operating current gives the circuit's nominal power."),
    dict(id="op_current_a", label="Operating current", group="Electrical system", kind="number", unit="A", tier="quant", applies=["electrical"], min=0, max=1000000, exclusive_min=True,
         why="With operating voltage gives the circuit's nominal power."),
    dict(id="fault_current_a", label="Prospective fault current", group="Electrical system", kind="number", unit="A", tier="quant", applies=["electrical"], min=0, max=10000000, exclusive_min=True,
         why="With the clearing time gives the let-through energy (I²t), the quantity used in the cited ignition-test methodology."),
    dict(id="clearing_ms", label="Fault clearing time of the protective device", group="Electrical system", kind="number", unit="ms", tier="quant", applies=["electrical"], min=0, max=1000000, exclusive_min=True,
         why="With the fault current gives the let-through energy (I²t)."),
    dict(id="fault_protection", label="Fault protection", group="Electrical system", kind="select", tier="detail", applies=["electrical"], options=_opts(
        ("characterised", "Protective devices specified and tested for this circuit"), ("specified", "Protective devices specified, not tested"),
        ("none", "No fault protection, or unknown")), why="A specified protection is a proposed mitigation; a tested one is evidence."),
    dict(id="power_isolation", label="Procedure to remove power from the affected equipment", group="Electrical system", kind="select", tier="detail", applies=["electrical", "battery"], options=_opts(
        ("verified", "Defined and verified (test or drill)"), ("defined", "Defined, not verified"), ("none", "Not defined")),
        why="The ISS response sequence in the cited brief includes removing electrical power to cease continuous ignition sources."),
    dict(id="redundancy", label="Redundancy and emergency power", group="Electrical system", kind="select", tier="detail", applies=["electrical"], options=_opts(
        ("defined", "Redundant power paths and emergency power defined"), ("partial", "Partly defined"), ("none", "None")),
        why="Determines what is lost when the circuit is de-energised."),
    dict(id="inspection", label="Inspection and maintenance history", group="Electrical system", kind="select", tier="detail", applies=["electrical"], options=_opts(
        ("documented", "Documented"), ("undocumented", "Not documented")), why="Condition of wiring and connections cannot be assessed without it."),
    # ---- Detection and response
    dict(id="detection_coverage", label="Fire detection coverage", group="Detection and response", kind="select", tier="detail", options=_opts(
        ("distributed", "Several detectors across the compartment"), ("single", "One zone or one detector"), ("gaps", "Coverage gaps or unconfirmed")),
        why="Time to detection depends on where detectors are."),
    dict(id="detection_signals", label="Fire signatures detected", group="Detection and response", kind="select", tier="detail", options=_opts(
        ("multi", "Smoke/particulate, combustion gas and temperature"), ("smoke_gas", "Smoke/particulate and combustion gas"),
        ("smoke", "Smoke/particulate only"), ("other", "Temperature or other only")),
        why="Fire emissions depend on the fuel, heating conditions, gravity and atmosphere."),
    dict(id="suppression", label="Fire suppression provisions", group="Detection and response", kind="select", tier="detail", options=_opts(
        ("both", "Fixed or installed system plus portable, access verified"), ("portable", "Portable extinguishers only"), ("limited", "Limited or unconfirmed")),
        why="Provisions differ in what they can reach and what they require of the crew."),
    dict(id="ppe", label="Crew breathing protection", group="Detection and response", kind="select", tier="detail", options=_opts(
        ("accessible", "Available and accessible; verified"), ("unverified", "Available; access not verified"), ("none", "Not available")),
        why="Combustion products can be immediately harmful at small concentrations."),
    dict(id="drills", label="Crew fire-response practice", group="Detection and response", kind="select", tier="detail", options=_opts(
        ("current", "Current"), ("overdue", "Overdue"), ("none", "None or unknown")), why="Response depends on practised procedures."),
    dict(id="postfire", label="Post-fire monitoring and clean-up", group="Detection and response", kind="select", tier="detail", options=_opts(
        ("defined", "Monitoring and clean-up plan defined"), ("partial", "Partial plan"), ("none", "No plan")),
        why="Combustion products can remain after flames are out."),
    # ---- Materials and other sources
    dict(id="materials", label="Material flammability evidence", group="Materials and other sources", kind="select", tier="detail", options=_opts(
        ("tested", "Tested for this atmosphere and gravity"), ("partial", "Partly tested"), ("untested", "Not tested, or older materials")),
        why="Flammability data apply only to the conditions tested."),
    dict(id="ignition_other", label="Other ignition sources considered", group="Materials and other sources", kind="select", tier="detail", options=_opts(
        ("low", "Few and well controlled"), ("typical", "Typical equipment"), ("elevated", "Unresolved faults or hot spots")),
        why="Used by the heuristic screening index."),
    dict(id="battery", label="Stored energy (batteries)", group="Materials and other sources", kind="select", tier="detail", applies=["battery"], options=_opts(
        ("managed", "Protected packs, managed inventory"), ("portable", "Portable rechargeable batteries aboard"), ("elevated", "Damaged or high-capacity concern")),
        why="Relevant to the battery hazard only."),
]
FIELD_BY_ID = {f["id"]: f for f in FIELDS}
GROUP_ORDER = ["Scenario", "Environment", "Mission constraints", "Electrical system", "Detection and response", "Materials and other sources"]
HAZARD_LABELS = {o["value"]: o["label"] for o in FIELD_BY_ID["hazard"]["options"]}
DEFAULT_QUESTION = "Which conditions in this scenario warrant review, and what information is missing?"


def option_label(field_id, value):
    for o in FIELD_BY_ID[field_id].get("options", []):
        if o["value"] == value:
            return o["label"]
    return str(value)


def applies(field, hazard):
    a = field.get("applies")
    return a is None or hazard in a


def public_schema():
    """The form definition the page renders (no behaviour, just data)."""
    return {"engineVersion": ENGINE_VERSION, "groups": GROUP_ORDER, "hazards": [o for o in FIELD_BY_ID["hazard"]["options"]],
            "fields": [{k: v for k, v in f.items()} for f in FIELDS], "defaultQuestion": DEFAULT_QUESTION}


# =====================================================================================================
# Input handling, units, significant figures
# =====================================================================================================

_NUM_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")


def count_sigfigs(text):
    """Significant figures of a number as written. Trailing zeros of an integer without a decimal point are
    treated as ambiguous and NOT counted (so '180' has two)."""
    s = str(text).strip().lstrip("+-")
    mant = re.split(r"[eE]", s)[0]
    if "." in mant:
        digits = mant.replace(".", "").lstrip("0")
        n = len(digits)
    else:
        n = len(mant.lstrip("0").rstrip("0"))
    return max(1, min(n if n else 1, 15))


def parse_number(value):
    """Return (float, sigfigs, text). Raises ValueError with a plain message."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError("must be a number")
    text = value.strip() if isinstance(value, str) else repr(value)
    if not _NUM_RE.match(text):
        raise ValueError("must be a plain number such as 28 or 0.5")
    x = float(text)
    if not math.isfinite(x):
        raise ValueError("must be a finite number")
    return x, count_sigfigs(text), text


def decimals_of(text):
    """Digits after the decimal point as written (used for differences, which keep the least precise decimal place)."""
    m = re.match(r"^[+-]?\d*\.?(\d*)(?:[eE][+-]?\d+)?$", str(text).strip())
    return len(m.group(1)) if m else 0


def sig_round(x, n):
    if x == 0 or not math.isfinite(x):
        return x
    exp = math.floor(math.log10(abs(x)))
    return round(x, n - 1 - exp)


_SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def _superscript(n):
    return str(n).translate(_SUP)


def fmt_sig(x, n):
    """Format x to n significant figures. Scientific notation is used when fixed notation would need padding zeros
    that imply more precision than n figures."""
    if x == 0:
        return "0"
    n = max(1, int(n))
    r = sig_round(x, n)
    exp = math.floor(math.log10(abs(r)))
    if exp >= n or exp < -3:
        return "%.*f × 10%s" % (n - 1, r / 10 ** exp, _superscript(exp))
    return "%.*f" % (max(0, n - 1 - exp), r)


def normalize_inputs(raw):
    """Validate user inputs. Returns {"values", "text", "sigfigs"}. Blank means NOT PROVIDED (None); nothing is
    ever filled in on the user's behalf. Raises InputError listing every problem."""
    errors = []
    if not isinstance(raw, dict):
        raise InputError([{"field": None, "message": "Inputs must be a JSON object"}])
    for k in raw:
        if k not in FIELD_BY_ID:
            errors.append({"field": str(k)[:40], "message": "Unknown input"})
    values, text, sigfigs = {}, {}, {}
    for f in FIELDS:
        fid, v = f["id"], raw.get(f["id"])
        blank = v is None or (isinstance(v, str) and v.strip() == "")
        if blank:
            values[fid] = f.get("default") if fid == "pressure_unit" else None
            continue
        try:
            if f["kind"] == "select":
                if not isinstance(v, str) or v not in {o["value"] for o in f["options"]}:
                    raise ValueError("is not one of the available options")
                values[fid] = v
            elif f["kind"] == "text":
                if not isinstance(v, str):
                    raise ValueError("must be text")
                values[fid] = re.sub(r"[\x00-\x1f\x7f]+", " ", v).strip()[: f.get("maxlen", 300)]
            else:
                x, sf, t = parse_number(v)
                lo, hi = f.get("min"), f.get("max")
                if lo is not None and (x <= lo if f.get("exclusive_min") else x < lo):
                    raise ValueError("must be greater than %s" % lo if f.get("exclusive_min") else "must be at least %s" % lo)
                if hi is not None and x > hi:
                    raise ValueError("must be at most %s" % hi)
                if f.get("integer") and x != int(x):
                    raise ValueError("must be a whole number")
                values[fid], text[fid], sigfigs[fid] = (int(x) if f.get("integer") else x), t, sf
        except ValueError as e:
            errors.append({"field": fid, "message": "%s %s" % (f["label"], e)})
    if errors:
        raise InputError(errors)
    return {"values": values, "text": text, "sigfigs": sigfigs}


def assessment_id(inp, basis=None):
    body = {"v": ENGINE_VERSION, "values": {k: v for k, v in inp["values"].items() if v is not None}}
    if basis:
        body["basis"] = basis  # only when given, so assessments made without a basis keep their earlier identifiers
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


# How the user knows an answer. "Not stated" is the default and is never treated as confirmation.
BASES = {"specification": "Specification or design document", "test": "Test or measurement", "analysis": "Analysis or simulation",
         "estimate": "My estimate", "assumption": "Working assumption"}
WEAK_BASES = ("estimate", "assumption")
# For these provisions the strongest option is a claim that something has been verified, tested or is complete.
STRONG_CLAIMS = {"fault_protection": "characterised", "power_isolation": "verified", "vent_control": "verified", "materials": "tested", "ppe": "accessible",
                 "suppression": "both", "drills": "current", "detection_coverage": "distributed", "redundancy": "defined", "inspection": "documented", "postfire": "defined"}


def normalize_basis(raw):
    """{field: basis code}. Unknown fields or codes are rejected; an empty value means 'not stated'."""
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise InputError([{"field": None, "message": "Basis must be a JSON object"}])
    out, errors = {}, []
    for k, v in raw.items():
        if k not in FIELD_BY_ID:
            errors.append({"field": str(k)[:40], "message": "Unknown input in basis"})
        elif v is None or (isinstance(v, str) and v.strip() == ""):
            continue
        elif not isinstance(v, str) or v not in BASES:
            errors.append({"field": k, "message": "Basis must be one of: " + ", ".join(BASES)})
        else:
            out[k] = v
    if errors:
        raise InputError(errors)
    return out


# ---- tiny dimensional-analysis helper: exponents of (kg, m, s, A) ------------------------------------
_UNITS = {"A": (0, 0, 0, 1), "V": (1, 2, -3, -1), "W": (1, 2, -3, 0), "J": (1, 2, -2, 0), "Pa": (1, -1, -2, 0), "kPa": (1, -1, -2, 0),
          "psi": (1, -1, -2, 0), "m3": (0, 3, 0, 0), "s": (0, 0, 1, 0), "ms": (0, 0, 1, 0), "min": (0, 0, 1, 0), "1": (0, 0, 0, 0)}


def dims(expr):
    """Dimension vector of a product/quotient of units, e.g. 'A^2*s' or 'm3/m3*min'."""
    out = [0, 0, 0, 0]
    sign = 1
    for tok in re.findall(r"[*/]|[A-Za-z0-9]+(?:\^-?\d+)?", expr):
        if tok == "*":
            sign = 1
            continue
        if tok == "/":
            sign = -1
            continue
        name, _, p = tok.partition("^")
        if name not in _UNITS:
            raise ValueError("unknown unit %s" % name)
        pw = int(p) if p else 1
        for i, e in enumerate(_UNITS[name]):
            out[i] += sign * pw * e
    return tuple(out)


def check_dimensions(expr, expected_unit):
    return dims(expr) == dims(expected_unit)


# =====================================================================================================
# Deterministic calculations
# =====================================================================================================

def _min_sf(inp, *ids):
    return min(inp["sigfigs"][i] for i in ids)


def derive(inp):
    """Dimension-checked calculations on supplied numbers. Each entry carries its formula, inputs, units,
    significant figures, assumptions and limits. A calculation that lacks inputs is simply not produced."""
    v, out = inp["values"], []

    def add(id_, label, value, unit, sf, formula, expr, expected, inputs, assumptions, limitations, evidence=None, extra=None):
        ok = check_dimensions(expr, expected)
        out.append({"id": id_, "label": label, "value": value, "unit": unit, "sigfigs": sf, "display": fmt_sig(value, sf),
                    "formula": formula, "dimensionalCheck": "consistent" if ok else "INCONSISTENT", "inputs": inputs,
                    "assumptions": assumptions, "limitations": limitations, "kind": "calculated estimate from supplied inputs",
                    "evidence": evidence or [], **(extra or {})})

    p_kpa = None
    if v["pressure"] is not None:
        if v["pressure_unit"] == "psia":
            p_kpa = v["pressure"] * PSIA_TO_KPA
            add("p_total_kpa", "Total cabin pressure in kPa", p_kpa, "kPa", inp["sigfigs"]["pressure"], "P(kPa) = P(psia) × 6.894757",
                "psi*1", "kPa", ["pressure"], ["Unit conversion factor is exact; precision follows the supplied value."], [])
        else:
            p_kpa = v["pressure"]
    if v["o2_percent"] is not None:
        dp = decimals_of(inp["text"]["o2_percent"])
        add("o2_excess_pp", "Oxygen fraction minus Earth-air reference", v["o2_percent"] - AIR_O2_PERCENT, "percentage points",
            min(inp["sigfigs"]["o2_percent"], 4), "Δx = x(O2) − %s%%" % AIR_O2_PERCENT, "1", "1", ["o2_percent"],
            ["Reference: dry air, %s%% oxygen by volume." % AIR_O2_PERCENT, "For a difference, the result keeps the decimal places of the supplied value (%d)." % dp],
            ["Says how far the oxygen fraction is from Earth air; says nothing about flammability by itself."],
            extra={"display": "%.*f" % (dp, v["o2_percent"] - AIR_O2_PERCENT), "sigfigs": None})
    if v["o2_percent"] is not None and p_kpa is not None:
        sf = _min_sf(inp, "o2_percent", "pressure")
        po2 = v["o2_percent"] / 100.0 * p_kpa
        add("po2_kpa", "Oxygen partial pressure", po2, "kPa", sf, "p(O2) = x(O2) × P(total)", "1*kPa", "kPa", ["o2_percent", "pressure"],
            ["Ideal-gas mixture: partial pressure = mole fraction × total pressure.", "Percent by volume is taken as mole fraction."],
            ["Flammability depends on oxygen fraction as well as partial pressure; this number alone does not rank two atmospheres."])
        ref = AIR_O2_PERCENT / 100.0 * SEA_LEVEL_KPA
        add("po2_ratio", "Oxygen partial pressure relative to Earth sea-level air", po2 / ref, "(ratio)", min(sf, 4), "p(O2) ÷ (0.2095 × 101.325 kPa)",
            "kPa/kPa", "1", ["o2_percent", "pressure"], ["Reference p(O2) = %s kPa (sea-level air)." % fmt_sig(ref, 4)], ["A ratio of conditions, not a risk measure."])
    if v["voltage_v"] is not None and v["op_current_a"] is not None:
        sf = _min_sf(inp, "voltage_v", "op_current_a")
        add("power_w", "Nominal circuit power", v["voltage_v"] * v["op_current_a"], "W", sf, "P = V × I", "V*A", "W", ["voltage_v", "op_current_a"],
            ["Steady operating values; no fault."], ["Not the power released in a fault or arc, which depends on fault impedance and arc behaviour."])
    if v["fault_current_a"] is not None and v["clearing_ms"] is not None:
        sf = _min_sf(inp, "fault_current_a", "clearing_ms")
        add("i2t", "Let-through energy of the fault (I²t)", v["fault_current_a"] ** 2 * v["clearing_ms"] / 1000.0, "A²·s", sf, "I²t = I(fault)² × t(clearing)",
            "A^2*ms", "A^2*s", ["fault_current_a", "clearing_ms"],
            ["The prospective fault current is constant for the whole clearing time.", "Millisecond-to-second conversion is exact (÷1000)."],
            ["Ignores arc voltage, current limiting and conductor heating.",
             "NOT compared with any ignition limit: the cited methodology reports thresholds that are specific to the materials and wire configurations tested, and Astroflare holds none."],
            evidence=["S04.c2"])
    if v["volume_m3"] is not None and v["vent_flow_m3_min"] is not None:
        sf = _min_sf(inp, "volume_m3", "vent_flow_m3_min")
        add("turnover_min", "Air turnover time of the compartment", v["volume_m3"] / v["vent_flow_m3_min"], "min", sf, "τ = V ÷ Q", "m3/m3*min", "min",
            ["volume_m3", "vent_flow_m3_min"], ["Well-mixed compartment."],
            ["A transport time scale only; it does not predict smoke concentration, detector response or flame behaviour."])
    if v["comm_delay_min"] is not None:
        add("rtt_min", "Minimum round-trip communication time", 2 * v["comm_delay_min"], "min", inp["sigfigs"]["comm_delay_min"] if v["comm_delay_min"] else 1,
            "RTT = 2 × one-way delay", "min", "min", ["comm_delay_min"], ["Symmetric one-way delay; no processing or queueing time."],
            ["A lower bound: the earliest a ground reply could arrive."])
    return out


# =====================================================================================================
# Findings
# =====================================================================================================

def finding(id_, kind, title, statement, basis, inputs, reasoning, relevance, limitations=None, evidence=None, needs=None, priority=50):
    return {"id": id_, "kind": kind, "title": title, "statement": statement, "basis": basis, "inputsUsed": inputs, "reasoning": reasoning,
            "relevance": relevance, "limitations": limitations or [], "evidence": evidence or [], "needs": needs or [], "priority": priority}


BASIS_TEXT = {"sourced": "Supported by cited sources (general statements)", "inference": "Inference from supplied inputs; no source cited",
              "calculation": "Deterministic calculation from supplied inputs", "input": "Restates a supplied input"}
KIND_TEXT = {"pathway": "Plausible hazard pathway (not a demonstrated failure mode)", "condition": "Condition warranting review",
             "context": "Context (no concern flagged by Astroflare's rules)", "gap": "Information gap"}


def run_rules(inp, derived):
    v = inp["values"]
    hz = v["hazard"]
    d = {x["id"]: x for x in derived}
    F = []
    add = F.append
    fire_hazard = hz in ("electrical", "battery", "material", "smoke")

    # ---- hazard pathway (labelled as plausible, not demonstrated)
    if hz == "electrical":
        add(finding("pathway_electrical", "pathway", "Plausible pathway: electrical overheating or arcing igniting insulation or nearby material",
                    "Electrical faults and wire-insulation combustion are described in the cited literature as a recognised ignition pathway in spacecraft. "
                    "For the circuit described here this is a plausible pathway only; the inputs do not demonstrate that it can occur or that it cannot.",
                    "sourced", ["hazard"],
                    "The sources describe wire insulation combustion as a likely cause of spacecraft fires, report Apollo-era work on wiring malfunction and current-overload flammability, and name electrical wiring among the most probable ignition sources in the Apollo 1 fire.",
                    "Defines the hazard pathway under investigation.",
                    ["The sources are general (drop-tower experiments, a 1971 paper, accident history). None characterises the circuit, materials or atmosphere described here.",
                     "A plausible pathway is not a measured failure rate or a prediction."],
                    ["S03.c1", "S05.c1", "S01.c7"], ["NS_ignition_test", "NS_review"], 10))
    elif hz == "battery":
        add(finding("pathway_battery", "pathway", "Plausible pathway: battery cell thermal runaway",
                    "Thermal runaway of lithium-ion cells is a recognised spacecraft battery hazard in NASA work cited here. For the batteries described here it is a plausible pathway only.",
                    "sourced", ["hazard"],
                    "The cited NASA material states that preventing single-cell thermal runaway has historically been emphasised over reducing the severity of a single-cell event, and that the battery safety standard was updated to require assessing severity; a propagation test of a non-flight ISS battery was performed.",
                    "Defines the hazard pathway under investigation.",
                    ["The sources concern ISS batteries; they do not characterise the batteries described here.", "The abstracts do not state test results."],
                    ["S13.c1", "S14.c1"], ["NS_battery_severity", "NS_review"], 10))
    elif hz == "material":
        add(finding("pathway_material", "pathway", "Plausible pathway: ignition of cabin materials",
                    "Ignition and flame spread over cabin materials depends on the material, the atmosphere and the gravity regime; the cited sources require material flammability to be assessed in the relevant atmosphere and gravity.",
                    "sourced", ["hazard"], "The technical brief states that material flammability must be assessed in relevant cabin atmospheres and gravity levels; the interim standard in the library covers flammability test methods.",
                    "Defines the hazard pathway under investigation.", ["No material, ignition source or geometry is specified, so no flame-spread statement is made.",
                                                                                     "A plausible pathway is not demonstrated for the materials described here."],
                    ["S01.c10", "S12.c1"], ["NS_material_tests", "NS_review"], 10))
    elif hz == "smoke":
        add(finding("pathway_smoke", "pathway", "Plausible pathway: persistent smoke or combustion products after a fire",
                    "Combustion products can remain after visible flames are controlled, and monitoring and clean-up are part of fire response in the cited NASA material.",
                    "sourced", ["hazard"], "The technical brief describes considerable post-fire clean-up and monitoring; an instrument paper states combustion-gas monitoring can give early warning and facilitate safe post-fire clean-up.",
                    "Defines the hazard pathway under investigation.", ["No specific fuel, quantity or compartment is given, so no concentration is estimated.",
                                                                                     "A plausible pathway is not demonstrated for the compartment described here."],
                    ["S01.c13", "S11.c1"], ["NS_postfire", "NS_review"], 10))

    # ---- atmosphere
    o2, P = v["o2_percent"], v["pressure"]
    if o2 is not None:
        pp = d["o2_excess_pp"]["value"]
        pp_disp = d["o2_excess_pp"]["display"]
        extra = ""
        if "po2_kpa" in d:
            extra = " The total pressure gives an oxygen partial pressure of %s kPa, %s times that of sea-level Earth air." % (d["po2_kpa"]["display"], d["po2_ratio"]["display"])
        if pp > O2_EQUAL_TOL_PP:
            add(finding("atm_o2", "condition", "Oxygen fraction is above Earth air",
                        "The supplied oxygen fraction is %s%% by volume, %s percentage points above the Earth-air reference of %s%%.%s" % (inp["text"]["o2_percent"], pp_disp, AIR_O2_PERCENT, extra),
                        "sourced", ["o2_percent", "pressure"],
                        "The cited technical brief states that in environments with higher oxygen content and/or pressure, materials that normally do not burn have lower ignition temperatures and burn more vigorously; a roadmap paper lists increased oxygen concentration among conditions beyond past operational experience. Material data obtained in Earth air therefore cannot be assumed to apply.",
                        "Determines which material test data are relevant to this scenario.",
                        ["The statements are general. They give no threshold or quantitative effect for the materials in this scenario.",
                         "A competing effect is reported: low-gravity flames can be suppressed more easily by dilution or lower total pressure. The net effect at this composition and pressure is unresolved (see competing evidence)."],
                        ["S01.c3", "S06.c1", "S02.c2"], ["NS_material_atm"], 40))
        else:
            rel_txt = "equal to Earth air within ±%s percentage points" % O2_EQUAL_TOL_PP if abs(pp) <= O2_EQUAL_TOL_PP else "below Earth air"
            add(finding("atm_o2", "context", "Oxygen fraction is %s" % ("about equal to Earth air" if abs(pp) <= O2_EQUAL_TOL_PP else "below Earth air"),
                        "The supplied oxygen fraction is %s%% by volume, %s (reference %s%%).%s This does not establish that Earth-based material data apply: total pressure and gravity may also differ." % (inp["text"]["o2_percent"], rel_txt, AIR_O2_PERCENT, extra),
                        "calculation", ["o2_percent", "pressure"], "Direct comparison with the reference value.", "Context for choosing applicable material data.",
                        ["A lower oxygen fraction does not by itself imply a lower hazard; other conditions are unchanged by this comparison."], [], [], 40))
    if P is not None:
        pk = d["p_total_kpa"]["value"] if "p_total_kpa" in d else P
        rel = (pk - SEA_LEVEL_KPA) / SEA_LEVEL_KPA
        if abs(rel) > PRESSURE_EQUAL_TOL:
            add(finding("atm_pressure", "condition", "Total pressure differs from sea-level Earth air",
                        "The supplied total pressure is %s kPa, %s sea-level pressure (101.325 kPa)." % (fmt_sig(pk, inp["sigfigs"]["pressure"]), "below" if rel < 0 else "above"),
                        "sourced", ["pressure"],
                        "The cited technical brief states design requirements must specify the permitted pressure and oxygen combinations and that materials must be assessed in the relevant atmosphere; the 1993 paper reports low-gravity flames can be suppressed more easily by decreasing total pressure.",
                        "Determines which test data are relevant.",
                        ["Pressure and oxygen fraction act together; the cited statements do not give the net effect for this combination."],
                        ["S01.c10", "S02.c2"], ["NS_material_atm"], 41))

    # ---- gravity
    g = v["gravity"]
    if g in ("micro", "lunar", "mars"):
        ev = ["S01.c2", "S02.c1", "S08.c1", "S08.c2", "S09.c1"] + (["S01.c8"] if g in ("lunar", "mars") else [])
        add(finding("gravity", "condition", "Reduced-gravity fire and smoke behaviour differs from Earth-based expectations",
                    "Gravity regime supplied: %s. Literature cited here reports that without buoyancy flames and smoke behave differently from normal gravity, and that fire-safety design has often relied on 1 g understanding." % option_label("gravity", g),
                    "sourced", ["gravity"],
                    "Cited sources report that without buoyancy flames burn equally in all directions, that thin-sheet materials show reduced flammability and flame spread in quiescent low gravity, that smoke particles can grow larger in low gravity, and that detectors were designed on normal-gravity data."
                    + (" For partial gravity the technical brief states no terrestrial facility can confirm ground-based low-gravity screening results." if g != "micro" else ""),
                    "Determines which test data, detector designs and flame-spread assumptions can be transferred.",
                    ["Several statements concern thin-sheet fuels or older experiments; they are not tests of this scenario.", "Large-scale reduced-gravity fire data are limited (see limitations)."],
                    ev, ["NS_partial_gravity" if g != "micro" else "NS_detect_perf"], 42))
    elif g == "earth":
        add(finding("gravity", "context", "Earth-like gravity", "Gravity regime supplied: Earth-like (1 g). Buoyancy-driven behaviour is present, so Earth-based fire data are more relevant in this respect; atmosphere, materials and ventilation may still differ.",
                    "input", ["gravity"], "Restates the supplied input.", "Context.", [], [], [], 42))

    # ---- ventilation
    vc = v["vent_control"]
    if vc is not None and g in ("micro", "lunar", "mars", None):
        if vc == "no":
            add(finding("vent_control", "condition", "Ventilation cannot be stopped independently for the affected compartment",
                        "Ventilation to the affected compartment cannot be stopped independently (as supplied). Forced airflow can supply a fire with the air it needs, according to the cited brief.",
                        "sourced", ["vent_control", "gravity"],
                        "The technical brief states ventilation fans can supply the air a fire needs and that the ISS response sequence terminates ventilation in the affected module to slow spread; a 1993 paper reports ventilating flow can greatly enhance flammability range and flame spread in low gravity.",
                        "Determines whether the ISS-style step of stopping ventilation is available in this design.",
                        ["Whether stopping ventilation is net beneficial also depends on detector placement and flow rates (see competing evidence).", "The ISS sequence is an example, not a requirement for this design."],
                        ["S01.c2", "S01.c6", "S02.c3"], ["NS_vent_study"], 50))
        elif vc == "unverified":
            add(finding("vent_control", "condition", "Ability to stop ventilation is not verified",
                        "Ventilation to the affected compartment is reported as stoppable, but this is not reported as verified. A proposed capability is not evidence that it works.",
                        "sourced", ["vent_control"], "The ISS response sequence in the technical brief includes terminating ventilation in the affected module; whether it works here is not shown by the inputs.",
                        "Determines whether the response step can be relied on.", ["Verification status is as reported by the user; Astroflare cannot check it."],
                        ["S01.c6"], ["NS_vent_study"], 50))
        else:
            add(finding("vent_control", "context", "Ventilation can be stopped (verified, as reported)",
                        "Ventilation to the affected compartment is reported as stoppable and verified. Stopping it has a trade-off: detection in the cited brief relies on airflow bringing smoke to detectors.",
                        "sourced", ["vent_control"], "The brief places smoke detectors in the ventilation system and states airflow is needed to make smoke detectable; it also lists stopping ventilation to slow fire spread.",
                        "Shows a design trade-off to analyse rather than a settled benefit.", ["Verification status is as reported by the user."], ["S01.c4", "S01.c6"], ["NS_vent_study"], 50))
    elif vc is None and fire_hazard and g in ("micro", "lunar", "mars"):
        add(finding("gap_vent", "gap", "Ventilation control not provided",
                    "Whether ventilation to the affected compartment can be stopped was not supplied, so no statement about ventilation response is made.", "input", ["vent_control"],
                    "Required to apply the ISS-style response step discussed in the cited brief.", "Limits the ventilation and detection assessment.", [], [], ["NS_vent_study"], 50))
    if "turnover_min" in d:
        add(finding("turnover", "context", "Air turnover time scale of the compartment",
                    "With %s m³ and %s m³/min the compartment air turns over in %s minutes (volume ÷ flow)." % (inp["text"]["volume_m3"], inp["text"]["vent_flow_m3_min"], d["turnover_min"]["display"]),
                    "calculation", ["volume_m3", "vent_flow_m3_min"], "Arithmetic on supplied values.", "Gives a transport time scale for comparing with detector response and response times.",
                    ["Does not predict smoke concentration or detector response; assumes a well-mixed compartment."], [], [], 51))

    # ---- mission and response context
    ab, ph = v["abort"], v["phase"]
    if ab in ("limited", "remote"):
        add(finding("abort", "condition", "Limited return or safe-haven options",
                    "Return or safe-haven options are %s." % ("limited" if ab == "limited" else "not available quickly"),
                    "sourced", ["abort"], "Inference: response would then rely on the vehicle's own resources. The technical brief lists no emergency resupply, limited stowage of suppressant and diluents, and delayed ground communications among deep-space challenges, and states current ISS solutions are not designed for long-duration missions.",
                    "Bears on how much of the response must be self-contained.", ["The brief describes challenges, not a quantified consequence for this scenario."], ["S01.c9"], ["NS_review"], 90))
    elif ab == "near":
        add(finding("abort", "context", "Quick return or safe haven available (as supplied)", "A quick return or safe haven is reported as available.", "input", ["abort"], "Restates the supplied input.", "Context.", ["Availability is as reported by the user."], [], [], 90))
    if ph == "dormant":
        add(finding("dormant", "condition", "Dormant or uncrewed interval",
                    "The phase supplied is a dormant/uncrewed interval, so no crew would be present to detect or respond.", "sourced", ["phase"],
                    "A NASA roadmap paper lists dormancy intervals among conditions beyond past operational experience, and the technical brief states automated systems are to be used where the crew could be absent.",
                    "Response would have to be automated or deferred.", ["Neither source gives a dormancy duration threshold or a design for this scenario."], ["S06.c1", "S01.c16"], ["NS_review"], 91))
    if v["duration_days"] is not None:
        add(finding("duration", "context", "Mission duration",
                    "Mission duration supplied: %s days. The cited roadmap paper lists extended duration among factors that expand the fire-safety parameter space but gives no duration threshold, so Astroflare does not classify this duration as extended or not." % inp["text"]["duration_days"],
                    "sourced", ["duration_days"], "Direct restatement with a pointer to the cited roadmap statement.", "Context.", ["Duration alone does not change any finding."], ["S06.c1"], [], 92))
    if "rtt_min" in d:
        add(finding("comm_delay", "context", "Communication delay with the ground",
                    "With a one-way delay of %s minutes, the earliest possible ground reply is %s minutes after a message is sent, so ground consultation cannot be part of any response step shorter than that." % (inp["text"]["comm_delay_min"], d["rtt_min"]["display"]),
                    "calculation", ["comm_delay_min"], "Round-trip time is twice the one-way delay (arithmetic). The technical brief also notes ground consultation may be of poor quality and delayed.",
                    "Shows which decisions must be made on board.", ["A lower bound; real delays include processing and queueing."], ["S01.c9"], ["NS_review"], 93))
    elif fire_hazard and ab in ("limited", "remote"):
        add(finding("gap_comm", "gap", "Communication delay not provided", "The communication delay to the ground was not supplied, so the shortest ground-reply time cannot be calculated.", "input", ["comm_delay_min"],
                    "Needed for the round-trip time calculation.", "Limits the response-timeline statement.", [], [], [], 93))

    # ---- detection
    dc, ds = v["detection_coverage"], v["detection_signals"]
    if dc in ("single", "gaps"):
        add(finding("detect_cov", "condition", "Detection coverage is limited",
                    "Detection coverage is %s. Time to detection depends on where detectors are relative to a fire." % ("one zone or one detector" if dc == "single" else "reported as having gaps or unconfirmed"),
                    "sourced", ["detection_coverage"], "The technical brief states detection depends on knowing where detectors should be located and the associated time to detection.",
                    "Bears on how quickly an event would be noticed.", ["No detector performance data were supplied."], ["S01.c11"], ["NS_detect_perf"], 60))
    elif dc == "distributed":
        add(finding("detect_cov", "context", "Detection coverage reported as distributed", "Several detectors across the compartment are reported. Astroflare cannot confirm detector performance.", "input", ["detection_coverage"], "Restates the supplied input.", "Context.", ["Reported, not verified, by the user."], ["S01.c11"], ["NS_detect_perf"], 60))
    if ds in ("smoke", "other"):
        add(finding("detect_sig", "condition", "Fire signatures detected are limited",
                    "Detection is supplied as %s." % ("smoke/particulate only" if ds == "smoke" else "temperature or other signatures only"),
                    "sourced", ["detection_signals"], "Cited sources state fire emissions depend on fuel type, heating conditions, gravity and atmosphere, that detectors must handle a wide variety of fires, and that spacecraft smoke detectors were designed on normal-gravity data.",
                    "Inference from the cited statement that emissions depend on heating conditions: overheating insulation may produce different emissions from a flaming fire. Which signatures appear first in this scenario is not established by the inputs.",
                    ["No emission data for the materials in this scenario were supplied."], ["S07.c1", "S07.c2", "S08.c1", "S01.c11"], ["NS_detect_perf"], 61))
    if ds in ("smoke", "other"):
        if True:
            add(finding("detect_gas", "condition", "No combustion-gas monitoring supplied",
                        "Combustion-gas monitoring is not part of the detection supplied. The cited brief describes carbon monoxide buildup as an additional early-warning source.", "sourced", ["detection_signals"],
                        "The technical brief states buildup of atmospheric gases, particularly carbon monoxide, is an additional early-warning source and that ISS uses continuous atmospheric sampling; an instrument paper describes combustion-product monitoring for early warning and post-fire clean-up.",
                        "Gas monitoring also informs post-fire clean-up.", ["The sources describe capability, not whether it is needed for this design."], ["S01.c5", "S11.c1"], ["NS_detect_perf"], 62))
    if dc is None and ds is None and fire_hazard:
        add(finding("gap_detect", "gap", "Fire detection not described", "Detection coverage and signatures were not supplied, so nothing is said about how an event would be detected.", "input", ["detection_coverage", "detection_signals"],
                    "Required to discuss time to detection.", "Limits the detection assessment.", [], [], ["NS_detect_perf"], 60))

    # ---- suppression, protection of crew, post-fire, drills, materials
    sp = v["suppression"]
    if sp in ("portable", "limited"):
        add(finding("suppression", "condition", "Suppression provisions are limited",
                    "Suppression is %s. Adequacy for this hazard (for example energised electrical equipment, access behind panels) is not assessed." % ("portable extinguishers only" if sp == "portable" else "limited or unconfirmed"),
                    "sourced", ["suppression"], "The technical brief states extinguishing equipment must be usable in microgravity, accessible, and must not create additional hazards, and that automated systems are needed where crews cannot extinguish a fire.",
                    "Bears on whether a detected event could be controlled.", ["No agent, quantity or access information was supplied."], ["S01.c12", "S01.c16"], ["NS_suppression"], 70))
    elif sp == "both":
        add(finding("suppression", "context", "Suppression reported as installed plus portable, access verified", "Reported by the user; Astroflare cannot confirm effectiveness for this hazard.", "input", ["suppression"], "Restates the supplied input.", "Context.", ["Reported, not verified, by the user."], ["S01.c12"], [], 70))
    pe = v["ppe"]
    if pe in ("unverified", "none"):
        add(finding("ppe", "condition", "Crew breathing protection is not confirmed as accessible",
                    "Crew breathing protection is %s." % ("available but access is not verified" if pe == "unverified" else "not available"),
                    "sourced", ["ppe"], "The technical brief states protective equipment must be donned in smoke or near a fire because even small concentrations of some combustion products can be immediately harmful.",
                    "Bears on crew exposure during response.", ["Verification status is as reported by the user."], ["S01.c12"], ["NS_ppe"], 75))
    pf = v["postfire"]
    if pf in ("partial", "none"):
        add(finding("postfire", "condition", "Post-fire monitoring and clean-up plan is incomplete",
                    "The post-fire monitoring and clean-up plan is %s." % ("partial" if pf == "partial" else "not defined"),
                    "sourced", ["postfire"], "The technical brief states considerable clean-up is required after all fire events, the state of the environment to be scrubbed must be specified, and the crew must be able to determine whether the atmosphere is safe enough to remove breathing apparatus.",
                    "Combustion products can remain after flames are out.", ["No contaminant levels or limits were supplied."], ["S01.c13", "S11.c1"], ["NS_postfire"], 80))
    dr = v["drills"]
    if dr in ("overdue", "none"):
        add(finding("drills", "condition", "Crew fire-response practice is not current",
                    "Crew fire-response practice is %s." % ("overdue" if dr == "overdue" else "absent or unknown"), "inference", ["drills"],
                    "Inference from the supplied input; no source is cited. A response that is not practised cannot be assumed to work as written.", "Bears on response reliability.",
                    ["Significance is not quantified."], [], ["NS_drills"], 85))
    mt = v["materials"]
    if mt in ("partial", "untested"):
        add(finding("materials", "condition", "Material flammability evidence is incomplete",
                    "Material flammability evidence is %s." % ("partial" if mt == "partial" else "absent or from older materials"), "sourced", ["materials"],
                    "The technical brief states material flammability must be assessed in the relevant cabin atmospheres and gravity levels; the interim standard in the library defines flammability test methods (its current revision must be checked).",
                    "Material data apply only to the conditions tested.", ["Which materials, atmospheres and gravity levels were tested was not supplied."], ["S01.c10", "S12.c1"], ["NS_material_atm"], 45))

    # ---- electrical-specific
    if hz == "electrical":
        if "power_w" in d:
            add(finding("power", "context", "Nominal circuit power",
                        "At %s V and %s A the circuit's nominal power is %s W." % (inp["text"]["voltage_v"], inp["text"]["op_current_a"], d["power_w"]["display"]),
                        "calculation", ["voltage_v", "op_current_a"], "P = V × I (units V·A = W, checked).", "Context for the energy available to a fault.",
                        ["Not the power released in a fault or arc."], [], [], 20))
        if "i2t" in d:
            add(finding("i2t", "condition", "Let-through energy of the fault was calculated but cannot be compared with an ignition limit",
                        "With a prospective fault current of %s A cleared in %s ms, I²t = %s A²·s. Astroflare holds no ignition thresholds, so this value is not judged high or low." % (inp["text"]["fault_current_a"], inp["text"]["clearing_ms"], d["i2t"]["display"]),
                        "sourced", ["fault_current_a", "clearing_ms"],
                        "The cited NASA test methodology seeks ignition energy-density thresholds expressed through I²t values for specific materials and wires, and names oxygen pressure, wire diameter, heat sinking and contained smoke volume among the factors needed to relate such thresholds to a real design.",
                        "Shows what additional data would turn this number into an ignition assessment.",
                        ["The cited thresholds are specific to the materials and configurations tested and are not available to Astroflare.", "The assumptions listed with the calculation apply."],
                        ["S04.c1", "S04.c2", "S04.c3"], ["NS_ignition_test"], 21))
        else:
            add(finding("gap_i2t", "gap", "Fault current and clearing time not both supplied",
                        "The prospective fault current and the protective device's clearing time were not both supplied, so the let-through energy (I²t) cannot be calculated.", "input", ["fault_current_a", "clearing_ms"],
                        "The cited ignition-test methodology uses I²t-based thresholds; without these values the circuit cannot be related to it.", "Blocks the main quantitative check for this hazard.", [], ["S04.c2"], ["NS_fault_char"], 22))
        fp = v["fault_protection"]
        if fp == "characterised":
            add(finding("fault_protection", "context", "Fault protection reported as specified and tested", "Protective devices are reported as specified and tested for this circuit. Test results were not supplied to Astroflare.", "input", ["fault_protection"], "Restates the supplied input.", "Context.", ["Reported, not verified, by the user."], [], [], 30))
        elif fp in ("specified", "none"):
            add(finding("fault_protection", "condition", "Fault protection is not demonstrated",
                        "Fault protection is %s. A specified protection is a proposed mitigation, not demonstrated performance." % ("specified but not tested" if fp == "specified" else "absent or unknown"),
                        "inference", ["fault_protection"], "Inference from the supplied input: how fast and how reliably a fault is cleared determines the let-through energy, which cannot be known without test data.", "Bears on how much energy a fault could deliver.",
                        ["No source is cited for this statement."], ["S04.c2"], ["NS_fault_char"], 30))
        else:
            add(finding("gap_fault_protection", "gap", "Fault protection not described", "Whether fault protection exists and has been tested was not supplied.", "input", ["fault_protection"], "Required to discuss how a fault would be cleared.", "Limits the electrical assessment.", [], [], ["NS_fault_char"], 30))
        pi = v["power_isolation"]
        if pi in ("defined", "none"):
            add(finding("power_isolation", "condition", "Ability to remove power is not verified" if pi == "defined" else "No procedure to remove power",
                        "The procedure to remove power from the affected equipment is %s." % ("defined but not verified" if pi == "defined" else "not defined"),
                        "sourced", ["power_isolation"], "The ISS response sequence in the technical brief includes manually removing electrical power from hardware in the affected module to cease continuous ignition sources.",
                        "An electrical ignition source can persist while the circuit remains energised.", ["The ISS sequence is an example, not a requirement for this design."], ["S01.c6"], ["NS_power_isolation"], 31))
        elif pi == "verified":
            add(finding("power_isolation", "context", "Ability to remove power reported as verified", "Reported by the user as defined and verified by test or drill; Astroflare cannot confirm it.", "input", ["power_isolation"], "Restates the supplied input.", "Context.", ["Reported, not verified, by the user."], ["S01.c6"], [], 31))
        else:
            add(finding("gap_power_isolation", "gap", "Power-removal procedure not described", "Whether power can be removed from the affected equipment was not supplied.", "input", ["power_isolation"], "The cited response sequence includes this step.", "Limits the response assessment.", [], ["S01.c6"], ["NS_power_isolation"], 31))
        if v["redundancy"] in ("none", "partial"):
            add(finding("redundancy", "condition", "Redundancy and emergency power are not fully defined",
                        "Redundancy and emergency power are %s, so the consequences of de-energising the circuit for other functions are not known." % ("partly defined" if v["redundancy"] == "partial" else "absent"),
                        "inference", ["redundancy"], "Inference from the supplied input; no source is cited.", "De-energising may be impractical if it removes essential functions.", ["Significance is not quantified."], [], ["NS_redundancy"], 32))
        elif v["redundancy"] is None:
            add(finding("gap_redundancy", "gap", "Redundancy and emergency power not described", "Redundant power paths and emergency power were not supplied.", "input", ["redundancy"], "Needed to judge the consequences of removing power.", "Limits the response assessment.", [], [], ["NS_redundancy"], 32))
        if v["inspection"] == "undocumented":
            add(finding("inspection", "condition", "No documented inspection history", "Inspection and maintenance history is not documented, so the condition of wiring and connections cannot be assessed.", "inference", ["inspection"], "Inference from the supplied input; no source is cited.", "Condition affects fault likelihood, which Astroflare does not estimate.", [], [], ["NS_inspection"], 33))
        elif v["inspection"] is None:
            add(finding("gap_inspection", "gap", "Inspection history not described", "Inspection and maintenance history was not supplied.", "input", ["inspection"], "Needed to judge the condition of wiring and connections.", "Limits the electrical assessment.", [], [], ["NS_inspection"], 33))
    if hz == "battery" and v["battery"] is not None:
        b = v["battery"]
        add(finding("battery", "condition" if b != "managed" else "context", "Stored-energy condition: %s" % option_label("battery", b).lower(),
                    "Stored energy is reported as: %s." % option_label("battery", b).lower(), "sourced" if b != "managed" else "input", ["battery"],
                    "NASA material cited here emphasises preventing single-cell runaway and assessing severity-reduction measures; the supplied input does not say how a thermal-runaway event would propagate or be contained.",
                    "Determines whether severity-reduction measures need to be examined.", ["The sources concern ISS batteries."], ["S13.c1"], ["NS_battery_severity"], 34))

    # ---- always, for fire-related hazards: the evidence base itself has gaps
    add(finding("evidence_scale", "context", "Large-scale reduced-gravity fire data are limited",
                "Cited NASA work states that the lack of experimental data at practical length scales and geometries has forced designers to rely on 1 g understanding, and that fire spread and growth cannot be expected to scale linearly.",
                "sourced", [], "Applies to every fire-related finding in this report.", "Limits how far any statement here can be extrapolated to a real vehicle.",
                ["The statements come from abstracts of Saffire experiment papers."], ["S09.c1", "S10.c1"], [], 100))
    return sorted(F, key=lambda f: (f["priority"], f["id"]))


# =====================================================================================================
# Next steps
# =====================================================================================================

NEXT_STEPS = {
    "NS_fault_char": ("information", "Obtain the prospective fault current and the protective device's clearing time for this circuit from the design or test records.",
                      "They are needed to calculate let-through energy (I²t) and to relate the circuit to the ignition-test methodology in the literature.", ["S04.c2"]),
    "NS_ignition_test": ("test", "Identify or commission electrical-fault ignition testing (wire-break-type) for the actual insulation, wire size and heat sinking in the intended atmosphere and gravity.",
                         "The cited methodology reports ignition thresholds that depend on material and configuration; no threshold is available without such data.", ["S04.c1", "S04.c3"]),
    "NS_material_atm": ("test", "Obtain flammability test data for the actual materials at the actual oxygen fraction, pressure and gravity (the current revision of NASA-STD-6001 is one reference for test methods).",
                        "Flammability data apply only to the conditions tested, and oxygen fraction and pressure act together.", ["S01.c10", "S12.c1"]),
    "NS_partial_gravity": ("test", "State how partial-gravity material flammability will be addressed, noting that ground-based low-gravity screening cannot confirm partial-gravity relevance.",
                           "The technical brief identifies this as a major gap for exploration missions.", ["S01.c8"]),
    "NS_detect_perf": ("test", "Demonstrate detector response to the emissions of the materials in this scenario (including overheated insulation) in the intended gravity and ventilation conditions.",
                       "Fire emissions depend on fuel, heating, gravity and atmosphere, and detectors were designed on normal-gravity data.", ["S07.c1", "S08.c1"]),
    "NS_vent_study": ("simulation", "Analyse airflow and smoke transport in the compartment with ventilation running and stopped, including detector response in each case.",
                      "Stopping ventilation can slow spread but detection relies on airflow; the net effect depends on layout and flow, which the sources do not resolve.", ["S01.c4", "S01.c6", "S02.c3"]),
    "NS_power_isolation": ("test", "Verify by test or drill that power to the affected equipment can be removed within the time needed, and record what other functions are lost.",
                           "Removing power ends a continuous electrical ignition source in the ISS sequence described in the brief.", ["S01.c6"]),
    "NS_redundancy": ("information", "Define redundant and emergency power arrangements and what is lost when the circuit is de-energised.", "Determines whether removing power is practical.", []),
    "NS_inspection": ("information", "Provide inspection and maintenance records for the wiring and connections.", "Condition of the hardware cannot be assessed without them.", []),
    "NS_suppression": ("information", "Describe suppression agents, quantities and access, including for energised equipment and areas behind panels.", "The brief requires equipment that is usable in microgravity, accessible and not hazardous.", ["S01.c12"]),
    "NS_ppe": ("test", "Verify by drill that crew breathing protection can be reached and donned within the time needed.", "Small concentrations of some combustion products can be immediately harmful.", ["S01.c12"]),
    "NS_postfire": ("information", "Define the post-fire monitoring ranges, clean-up method and the criteria for removing breathing protection.", "Combustion products can remain after flames are out.", ["S01.c13", "S11.c1"]),
    "NS_drills": ("information", "Schedule and record fire-response practice for this scenario.", "Response reliability depends on practised procedures.", []),
    "NS_battery_severity": ("test", "Assess thermal-runaway severity and propagation for the actual batteries and identify severity-reduction measures.", "The cited battery work emphasises assessing severity, not only preventing single-cell runaway.", ["S13.c1", "S14.c1"]),
    "NS_material_tests": ("test", "Specify the materials and ignition sources of concern and obtain flammability data for them.", "No material or ignition source was specified.", ["S01.c10"]),
    "NS_review": ("independent_review", "Submit this scenario, its inputs and these findings to qualified, independent fire-safety review before relying on any conclusion.",
                  "Astroflare has not been validated or reviewed; its output is a screening aid, not a safety determination.", []),
}


def build_next_steps(findings, inp):
    seen, out = [], []
    for f in findings:
        if f["kind"] in ("condition", "gap", "pathway"):
            for n in f["needs"]:
                if n not in seen:
                    seen.append(n)
    if "NS_review" not in seen:
        seen.append("NS_review")
    for n in seen:
        cat, action, why, ev = NEXT_STEPS[n]
        out.append({"id": n, "category": cat, "action": action, "why": why, "evidence": ev})
    order = {"information": 0, "calculation": 1, "simulation": 2, "test": 3, "independent_review": 4}
    return sorted(out, key=lambda s: (order[s["category"]], s["id"]))


# =====================================================================================================
# Heuristic screening index (legacy formula, de-fanged)
# =====================================================================================================

INDEX_TABLES = {
    "materials": ({"tested": 2, "partial": 9, "untested": 16}, 16, "materials"),
    "ignition_other": ({"low": 2, "typical": 7, "elevated": 12}, 12, "ignition_other"),
    "battery": ({"managed": 2, "portable": 7, "elevated": 14}, 14, "battery"),
    "detection": ({"distributed": 2, "single": 8, "gaps": 14}, 14, "detection_coverage"),
    "suppression": ({"both": 2, "portable": 7, "limited": 13}, 13, "suppression"),
    "isolation": ({"verified": 1, "defined": 5, "none": 10}, 10, "power_isolation"),
    "postfire": ({"defined": 1, "partial": 5, "none": 10}, 10, "postfire"),
    "abort": ({"near": 2, "limited": 6, "remote": 10}, 10, "abort"),
    "training": ({"current": 1, "overdue": 4, "none": 6}, 6, "drills"),
}
INDEX_APPLICABILITY = {"battery": ["battery"], "isolation": ["electrical", "battery"]}
VENT_POINTS = {"verified": 3, "unverified": 6, "no": 10}
GRAVITY_POINTS = {"micro": 4, "lunar": 3, "mars": 2, "earth": 0}
PHASE_POINTS = {"dormant": 2, "airlock": 1, "transit": 0, "surface": 0}


def screening_index(inp):
    """The original heuristic, kept so it can be inspected, but: every point value is a developer choice, the
    result is ordinal, it is NOT calibrated, NOT a probability and NOT comparable across hazard types. It is only
    computed when every input it needs was supplied; missing inputs are never replaced with defaults."""
    v, hz = inp["values"], inp["values"]["hazard"]
    base = {"label": INDEX_LABEL, "validated": False, "calibrated": False, "scope": "Comparing input sets for the SAME hazard type only.",
            "meaning": "Sum of developer-chosen points for supplied conditions, out of the maximum for the factors that apply to this hazard. Higher means more open or less-protected conditions among the factors counted. It is not a probability, not a measure of severity and carries no pass/fail meaning.",
            "changesFromEarlierVersions": "Earlier versions substituted default inputs when none were supplied, added a hazard-type constant and a battery term to every hazard, converted the total to a 0-100 score and applied threshold labels. None of that is done now, so earlier scores are not comparable."}
    if hz is None:
        return dict(base, computed=False, reason="No hazard selected.", factors=[], missing=[])
    factors, missing = [], []

    def need(*ids):
        m = [i for i in ids if v[i] is None]
        missing.extend(m)
        return not m

    if need("o2_percent"):
        factors.append(("Cabin atmosphere", max(0.0, min(22.0, (v["o2_percent"] - 21) * 1.65)), 22, "o2_percent", "clamp((O2% − 21) × 1.65, 0, 22)"))
    for key, (table, mx, fid) in INDEX_TABLES.items():
        if key in INDEX_APPLICABILITY and hz not in INDEX_APPLICABILITY[key]:
            continue
        if need(fid):
            factors.append((FIELD_BY_ID[fid]["label"], table[v[fid]], mx, fid, "table lookup"))
    if need("vent_control", "gravity"):
        factors.append(("Airflow and gravity", VENT_POINTS[v["vent_control"]] + GRAVITY_POINTS[v["gravity"]], 14, "vent_control + gravity", "ventilation points + gravity points"))
    if need("duration_days", "crew", "phase"):
        dur = max(0.0, min(6.0, math.log2(v["duration_days"] / 30 + 1) * 1.05))
        crew = max(0.0, min(3.2, (v["crew"] - 4) * 0.4))
        factors.append(("Mission length and crew", dur + crew + PHASE_POINTS[v["phase"]], 11.2, "duration_days + crew + phase", "clamp(log2(days/30+1)×1.05, 0, 6) + clamp((crew−4)×0.4, 0, 3.2) + phase points"))
    if missing:
        return dict(base, computed=False, reason="Not computed because these inputs were not supplied: %s." % ", ".join(FIELD_BY_ID[m]["label"] for m in dict.fromkeys(missing)),
                    factors=[], missing=list(dict.fromkeys(missing)))
    raw, mx = sum(f[1] for f in factors), sum(f[2] for f in factors)
    return dict(base, computed=True, value=int(round(raw)), maximum=int(round(mx)), unit="points",
                factors=[{"name": n, "points": round(p, 1), "maximum": m, "inputs": i, "rule": r} for n, p, m, i, r in factors], missing=[], reason=None)


# =====================================================================================================
# Protective layers: what the user REPORTED for each layer (never a rating)
# =====================================================================================================

LAYERS = [
    ("Prevent", ["materials", "fault_protection", "inspection", "ignition_other"]),
    ("Detect", ["detection_coverage", "detection_signals"]),
    ("Isolate and control", ["power_isolation", "vent_control", "redundancy"]),
    ("Suppress and protect", ["suppression", "ppe"]),
    ("Respond and recover", ["postfire", "drills"]),
]
# Fields whose options run from most to least complete in the order listed in FIELDS (first option = reported complete).
_ORDERED_COMPLETENESS = {"materials", "fault_protection", "inspection", "detection_coverage", "detection_signals", "power_isolation", "vent_control",
                         "redundancy", "suppression", "ppe", "postfire", "drills"}
_LEVEL_TEXT = {"complete": "Reported as complete or verified", "partial": "Reported as partial or not verified", "absent": "Reported as absent, limited or unknown",
               "not_provided": "Not provided", "info": "Reported (no completeness scale)"}


def protective_layers(inp):
    """The layered-protection view (prevent, detect, isolate, suppress, recover) as a table of the user's own
    statements. The level shown is where the user's choice sits on that input's scale; it is not a rating of
    effectiveness and nothing is checked by Astroflare."""
    v, hz = inp["values"], inp["values"]["hazard"]
    out = []
    for layer, ids in LAYERS:
        items = []
        for fid in ids:
            f = FIELD_BY_ID[fid]
            if hz is not None and not applies(f, hz):
                continue
            if v[fid] is None:
                items.append({"id": fid, "label": f["label"], "display": "Not provided", "level": "not_provided", "levelText": _LEVEL_TEXT["not_provided"]})
                continue
            if fid in _ORDERED_COMPLETENESS:
                values = [o["value"] for o in f["options"]]
                pos = values.index(v[fid])
                level = "complete" if pos == 0 else ("absent" if pos == len(values) - 1 else "partial")
            else:
                level = "info"
            items.append({"id": fid, "label": f["label"], "display": option_label(fid, v[fid]), "level": level, "levelText": _LEVEL_TEXT[level]})
        out.append({"layer": layer, "items": items})
    return out


# =====================================================================================================
# Assembly
# =====================================================================================================

def describe_inputs(inp):
    v, hz = inp["values"], inp["values"]["hazard"]
    supplied, missing, na = [], [], []
    for f in FIELDS:
        fid = f["id"]
        if fid == "pressure_unit":
            continue
        if hz is not None and not applies(f, hz):
            if v[fid] is not None:
                na.append({"id": fid, "label": f["label"], "reason": "Not applicable to the selected hazard; it was supplied but not used."})
            continue
        if v[fid] is None:
            if fid == "question" or (hz is None and f["tier"] != "core"):
                continue
            missing.append({"id": fid, "label": f["label"], "tier": f["tier"], "why": f["why"], "group": f["group"]})
            continue
        if f["kind"] == "select":
            disp = option_label(fid, v[fid])
        elif f["kind"] == "text":
            disp = v[fid]
        else:
            unit = v["pressure_unit"] if fid == "pressure" else f.get("unit", "")
            disp = ("%s %s" % (inp["text"][fid], unit)).strip()
        supplied.append({"id": fid, "label": f["label"], "value": v[fid], "display": disp, "group": f["group"]})
    return supplied, missing, na


def assumptions_for(inp, derived):
    out = ["Astroflare applies only the rules documented in the Method section to the inputs you supply; it does not model combustion, fire growth, smoke transport or toxicology.",
           "Reference atmosphere for comparisons: dry Earth air, %s%% oxygen by volume, at %s kPa (one standard atmosphere). Values within ±%s percentage points of oxygen, or ±%s%% of the reference pressure, are treated as equal to it; these tolerances are comparison conventions, not hazard thresholds."
           % (AIR_O2_PERCENT, SEA_LEVEL_KPA, O2_EQUAL_TOL_PP, int(PRESSURE_EQUAL_TOL * 100)),
           "Statements marked as reported (for example 'verified') are the user's description; Astroflare cannot check them."]
    for d in derived:
        for a in d["assumptions"]:
            out.append("%s: %s" % (d["label"], a))
    return list(dict.fromkeys(out))


def dimensions_block(inp, supplied, missing, findings):
    """Keeps the separate questions separate: what hazard, how bad, how likely, what modifies consequences,
    how complete the information is, what the evidence base is, and what uncertainty is measured."""
    core_total = sum(1 for f in FIELDS if f["tier"] == "core")
    core_missing = sum(1 for m in missing if m["tier"] == "core")
    applicable = len(supplied) + len(missing) - (1 if inp["values"]["question"] else 0)
    n_supplied = len(supplied) - (1 if inp["values"]["question"] else 0)
    return {
        "hazardIdentification": {"status": "from user selection", "detail": HAZARD_LABELS.get(inp["values"]["hazard"], "Not selected") + " (a what-if pathway, not a prediction)."},
        "severity": {"status": "not assessed", "detail": "Requires scenario-specific consequence analysis (fire growth, toxic products, crew exposure) that Astroflare does not perform."},
        "likelihood": {"status": "not assessed", "detail": "No fault frequency, failure rate or probability is supplied or held, and none is estimated."},
        "consequenceModifiers": {"status": "listed, not scored", "detail": "Factors that may change consequences if an event occurred (return options, communication delay, crew presence, protection and response provisions) are listed in the findings; they are not combined into a severity estimate."},
        "informationCompleteness": {"status": "measured count", "detail": "%d of %d applicable inputs supplied; %d of %d required for screening supplied." % (n_supplied, applicable, core_total - core_missing, core_total)},
        "evidenceBase": {"status": "described, not graded", "detail": "The number of sources does not measure the strength of evidence. Sources are general literature; none tests this design."},
        "measuredUncertainty": {"status": "none available", "detail": "No uncertainty or confidence interval is computed, and no automated confidence statement is used as a substitute."},
    }


def restrict_to_applicable(inp):
    """A copy of the inputs in which values that do not apply to the selected hazard are treated as not provided,
    so the statement that such inputs are "supplied but not used" is true of every calculation and rule."""
    hz = inp["values"]["hazard"]
    values = dict(inp["values"])
    for f in FIELDS:
        if f["id"] != "pressure_unit" and hz is not None and not applies(f, hz):
            values[f["id"]] = None
    return {**inp, "values": values}


def attach_basis(supplied, basis):
    """Adds the user's stated basis to each supplied input and returns the effective {field: basis} map."""
    eff = {}
    for s in supplied:
        b = basis.get(s["id"])
        s["basis"], s["basisLabel"] = b, BASES.get(b, "Not stated")
        if b:
            eff[s["id"]] = b
    return eff


def basis_block(supplied, eff):
    items = [s for s in supplied if s["id"] != "question"]
    return {"byInput": eff, "stated": len(eff), "notStated": len(items) - len(eff),
            "estimatesOrAssumptions": [s["label"] for s in items if eff.get(s["id"]) in WEAK_BASES],
            "note": "The basis is what the user said supports each answer. Astroflare records it and flags weak support; it cannot check it."}


def basis_limitations(inp, supplied, eff):
    out = []
    v, label = inp["values"], {s["id"]: s["label"] for s in supplied}
    weak = [label[k] for k, b in eff.items() if b in WEAK_BASES and k in label]
    if weak:
        out.append("%d supplied input%s %s the user's estimate or working assumption (%s). Calculations and findings that use %s are only as reliable as %s." % (
            len(weak), "" if len(weak) == 1 else "s", "is" if len(weak) == 1 else "are", "; ".join(weak), "it" if len(weak) == 1 else "them", "that estimate" if len(weak) == 1 else "those estimates"))
    strong = [k for k, val in STRONG_CLAIMS.items() if v.get(k) == val and k in label]
    contradicted = [k for k in strong if eff.get(k) in WEAK_BASES]
    unstated = [k for k in strong if k not in eff]
    if contradicted:
        out.append("Provisions reported at their strongest level but supported only by an estimate or assumption, so they should be treated as unverified: %s." % "; ".join(label[k] for k in contradicted))
    if unstated:
        out.append("Provisions reported at their strongest level without a stated basis (Astroflare cannot check them): %s." % "; ".join(label[k] for k in unstated))
    return out


def assess(raw_inputs, ev=None, today=None, basis=None):
    """Full deterministic assessment of the supplied inputs. Raises InputError for invalid inputs.
    `basis` optionally maps input ids to how the user knows the answer (see BASES); it is recorded and used to flag
    weak support, but never changes a calculation or a rule."""
    ev = ev or evidence_lib.default_evidence()
    today = today or date.today()
    inp = normalize_inputs(raw_inputs)
    bas = normalize_basis(basis)
    v = inp["values"]
    supplied, missing, not_applicable = describe_inputs(inp)
    eff = attach_basis(supplied, bas)
    base = {"schemaVersion": 1, "engineVersion": ENGINE_VERSION, "assessmentId": assessment_id(inp, eff)}
    q = v["question"]
    base["question"] = {"text": q or DEFAULT_QUESTION, "isDefault": not q}
    base["inputs"] = {"supplied": supplied, "missing": missing, "notApplicable": not_applicable}
    base["basis"] = basis_block(supplied, eff)
    if v["hazard"] is None:
        base.update({"status": {"code": "not_assessed", "label": "Not assessed", "reasons": ["No hazard was selected, so no rules can be applied."],
                                "checks": {"quantitativeChecks": 0, "evidenceStatements": 0, "sourcesCited": 0, "sourcesAbstractOnly": 0, "independentValidation": "Not performed",
                                           "literatureReview": "Not performed: Astroflare cites a curated list and does not search the literature."}},
                     "derived": [], "findings": [], "nextSteps": [], "screeningIndex": screening_index(inp), "layers": protective_layers(inp),
                     "dimensions": dimensions_block(inp, supplied, missing, []), "assumptions": assumptions_for(inp, []),
                     "evidence": {"sources": [], "claims": [], "tensions": [], "unknownClaimIds": []},
                     "limitations": static_limitations(), "summary": {"text": "No assessment: select the hazard you want to investigate. Nothing is assumed in its absence.", "principal": [], "unresolved": None}})
        return base
    inp = restrict_to_applicable(inp)
    derived = derive(inp)
    for d in derived:
        d["inputBasis"] = {i: eff.get(i) or "not stated" for i in d["inputs"]}
    findings = run_rules(inp, derived)
    next_steps = build_next_steps(findings, inp)
    cited_ids = [c for f in findings for c in f["evidence"]] + [c for d in derived for c in d["evidence"]] + [c for s in next_steps for c in s["evidence"]]
    cite = ev.cite(cited_ids, today)
    core_missing = [m for m in missing if m["tier"] == "core"]
    n_claims = len(cite["claims"])
    if core_missing:
        code, label = "incomplete", "Incomplete screening"
        reasons = ["Required inputs not supplied: %s." % ", ".join(m["label"] for m in core_missing)]
    else:
        code, label = "preliminary", "Preliminary screening"
        reasons = ["All inputs required for screening were supplied; %d further inputs were not." % len([m for m in missing if m["tier"] != "core"])]
    reasons.append("Findings come from fixed review rules applied to the supplied inputs and to general literature; no experiment, simulation or independent review was performed.")
    if cite["unknown"]:
        reasons.append("Some cited statements could not be retrieved from the source library; see Limitations.")
    abstract_only = [s["id"] for s in cite["sources"] if s["review"]["depth"] == "abstract"]
    checks = {"quantitativeChecks": len(derived), "evidenceStatements": n_claims, "sourcesCited": len(cite["sources"]), "sourcesAbstractOnly": len(abstract_only),
              "independentValidation": "Not performed", "literatureReview": "Not performed: Astroflare cites a curated list and does not search the literature."}
    status = {"code": code, "label": label, "reasons": reasons, "checks": checks}
    summary = build_summary(inp, findings, missing, core_missing, derived, code)
    base.update({"status": status, "derived": derived, "findings": findings, "nextSteps": next_steps, "screeningIndex": screening_index(inp), "layers": protective_layers(inp),
                 "dimensions": dimensions_block(inp, supplied, missing, findings), "assumptions": assumptions_for(inp, derived),
                 "evidence": {"sources": cite["sources"], "claims": [{"id": c["id"], "sourceId": c["source_id"], "topic": c["topic"], "text": c["text"]} for c in cite["claims"]],
                              "tensions": [{"id": t["id"], "topic": t["topic"], "claims": t["claims"], "note": t["note"]} for t in cite["tensions"]], "unknownClaimIds": cite["unknown"]},
                 "limitations": static_limitations() + dynamic_limitations(inp, missing, cite) + basis_limitations(inp, supplied, eff), "summary": summary})
    return base


def static_limitations():
    return ["Astroflare has not been validated against experiments and has not been reviewed by a qualified safety authority. It is a screening and evidence-organising aid, not a safety determination.",
            "No probability, frequency, severity, margin or confidence interval is estimated.",
            "A low number of flagged conditions does not mean the spacecraft is safe, and a high number does not mean an incident is likely: flags reflect which conditions the rules recognise in the supplied inputs.",
            "A proposed mitigation is not a demonstrated mitigation. Provisions are reported as the user described them and are not checked.",
            "Cited statements are general. They are not tests of the design described and may be outdated or specific to conditions that differ from this scenario."]


def dynamic_limitations(inp, missing, cite):
    out = []
    if missing:
        out.append("%d applicable inputs were not supplied; conclusions that depend on them are not drawn (see Information gaps)." % len(missing))
    if cite["unknown"]:
        out.append("%d cited statement%s could not be found in the source library and %s omitted from the evidence list (%s). The findings that rely on %s are therefore not backed by a retrievable source here."
                   % (len(cite["unknown"]), "" if len(cite["unknown"]) == 1 else "s", "was" if len(cite["unknown"]) == 1 else "were", ", ".join(cite["unknown"]),
                      "it" if len(cite["unknown"]) == 1 else "them"))
    if not cite["sources"]:
        out.append("No source could be retrieved, so no statement in this report is traceable to a source. No literature review was performed.")
    ab = [s for s in cite["sources"] if s["review"]["depth"] == "abstract"]
    if ab:
        out.append("%d of the %d cited sources were reviewed at abstract level only; their full text was not read." % (len(ab), len(cite["sources"])))
    old = [s for s in cite["sources"] if s.get("olderThanYears")]
    if old:
        out.append("Sources published %d or more years ago: %s. Age says nothing about correctness, but conditions and methods may have changed." % (evidence_lib.STALE_YEARS, ", ".join(s["id"] for s in old)))
    for t in cite["tensions"]:
        out.append("Competing considerations (%s): %s" % (t["topic"], t["note"]))
    return out


def build_summary(inp, findings, missing, core_missing, derived, code):
    v = inp["values"]
    conds = [f for f in findings if f["kind"] == "condition"]
    gaps = [f for f in findings if f["kind"] == "gap"]
    pathway = next((f for f in findings if f["kind"] == "pathway"), None)
    top = [f["title"] for f in conds[:3]]
    p = []
    p.append("Scenario: %s. This is a preliminary screening of the inputs supplied, not a risk estimate." % HAZARD_LABELS[v["hazard"]].lower())
    answer = "Screening result: %d condition%s warrant%s review and %d information gap%s limit the assessment." % (
        len(conds), "" if len(conds) == 1 else "s", "s" if len(conds) == 1 else "", len(gaps), "" if len(gaps) == 1 else "s")
    if top:
        answer += " Conditions flagged: %s%s." % ("; ".join(t[0].lower() + t[1:] for t in top), " and %d more" % (len(conds) - 3) if len(conds) > 3 else "")
    p.append(answer)
    unresolved = None
    cand = gaps or conds
    if core_missing:
        unresolved = "Required inputs not supplied: %s." % ", ".join(m["label"] for m in core_missing)
    elif cand:
        unresolved = cand[0]["title"] + "."
    if unresolved:
        un = unresolved.rstrip(".")
        p.append("Most consequential unresolved issue: %s (the order of items is presentational, not a ranking of risk)." % (un[0].lower() + un[1:]))
    p.append("Evidence limitations: findings rest on general NASA literature, mostly reviewed at abstract level, not on tests of this design; no probability or severity is estimated and no independent validation has been performed.")
    if pathway:
        p.append("The hazard pathway is a plausible one drawn from the literature, not a demonstrated failure mode of this system.")
    return {"text": " ".join(p), "paragraphs": p, "principal": top, "unresolved": unresolved, "conditions": len(conds), "gaps": len(gaps)}


def compare_assessments(a, b):
    """What changed between two assessments (baseline a, current b): inputs, findings and index."""
    sa = {x["id"]: x["display"] for x in a["inputs"]["supplied"]}
    sb = {x["id"]: x["display"] for x in b["inputs"]["supplied"]}
    labels = {x["id"]: x["label"] for x in a["inputs"]["supplied"] + b["inputs"]["supplied"] + a["inputs"]["missing"] + b["inputs"]["missing"]}
    changed = [{"id": k, "label": labels.get(k, k), "from": sa.get(k, "not provided"), "to": sb.get(k, "not provided")} for k in sorted(set(sa) | set(sb)) if sa.get(k) != sb.get(k)]
    fa = {f["id"]: f for f in a["findings"] if f["kind"] in ("condition", "gap")}
    fb = {f["id"]: f for f in b["findings"] if f["kind"] in ("condition", "gap")}
    ia, ib = a["screeningIndex"], b["screeningIndex"]
    delta = ib["value"] - ia["value"] if ia.get("computed") and ib.get("computed") and ia["maximum"] == ib["maximum"] else None
    return {"changedInputs": changed, "findingsAdded": [fb[k]["title"] for k in fb if k not in fa], "findingsRemoved": [fa[k]["title"] for k in fa if k not in fb],
            "indexDelta": delta, "indexNote": None if delta is not None else "The heuristic index was not compared because it was not computed for both input sets or the factors counted differ."}


# =====================================================================================================
# Examples (illustrative inputs, NOT mission data)
# =====================================================================================================

EXAMPLES = [
    {"id": "electrical_transit", "label": "180-day deep-space transit: electrical overheating (illustrative)",
     "note": "Example inputs for demonstration and regression testing. They are not mission data. Several inputs are deliberately left out to show how gaps are reported.",
     "inputs": {"question": "What conditions in a 180-day deep-space transit warrant review for an electrical-overheating event, and what information is missing?",
                "hazard": "electrical", "habitat": "transit", "phase": "transit", "gravity": "micro", "o2_percent": "21.0", "pressure": "14.7", "pressure_unit": "psia",
                "volume_m3": "30", "vent_flow_m3_min": "20", "vent_control": "unverified", "duration_days": "180", "crew": "4", "abort": "remote", "comm_delay_min": "12",
                "equip_type": "distribution", "voltage_v": "28", "op_current_a": "12", "fault_protection": "specified", "power_isolation": "defined",
                "detection_coverage": "single", "detection_signals": "smoke", "suppression": "portable", "ppe": "unverified", "drills": "current", "postfire": "partial",
                "materials": "partial", "ignition_other": "typical"}},
    {"id": "electrical_transit_complete", "label": "Same scenario with fault-protection data added (illustrative)",
     "note": "Adds illustrative fault current and clearing time so the let-through energy can be calculated. Values are examples, not data.",
     "inputs": {"question": "", "hazard": "electrical", "habitat": "transit", "phase": "transit", "gravity": "micro", "o2_percent": "21.0", "pressure": "14.7", "pressure_unit": "psia",
                "volume_m3": "30", "vent_flow_m3_min": "20", "vent_control": "unverified", "duration_days": "180", "crew": "4", "abort": "remote", "comm_delay_min": "12",
                "equip_type": "distribution", "voltage_v": "28", "op_current_a": "12", "fault_current_a": "150", "clearing_ms": "5", "fault_protection": "specified",
                "power_isolation": "defined", "redundancy": "partial", "inspection": "undocumented", "detection_coverage": "single", "detection_signals": "smoke",
                "suppression": "portable", "ppe": "unverified", "drills": "current", "postfire": "partial", "materials": "partial", "ignition_other": "typical"}},
    {"id": "lunar_battery", "label": "Lunar surface habitat: battery event (illustrative)", "note": "Example inputs, not mission data.",
     "inputs": {"hazard": "battery", "habitat": "lunar", "phase": "surface", "gravity": "lunar", "o2_percent": "26.5", "pressure": "10.2", "pressure_unit": "psia",
                "duration_days": "60", "crew": "4", "abort": "limited", "battery": "portable", "power_isolation": "defined", "detection_coverage": "single",
                "detection_signals": "smoke", "suppression": "portable", "ppe": "unverified", "postfire": "partial", "materials": "partial", "drills": "current",
                "ignition_other": "typical", "vent_control": "unverified"}},
    {"id": "mars_material", "label": "Mars surface habitat: cabin material ignition (illustrative)", "note": "Example inputs, not mission data.",
     "inputs": {"hazard": "material", "habitat": "mars", "phase": "surface", "gravity": "mars", "o2_percent": "26.5", "pressure": "10.2", "pressure_unit": "psia",
                "duration_days": "500", "crew": "6", "abort": "remote", "materials": "partial", "detection_coverage": "single", "detection_signals": "smoke_gas",
                "suppression": "portable", "ppe": "unverified", "drills": "overdue", "postfire": "partial", "ignition_other": "typical", "vent_control": "unverified"}},
]
