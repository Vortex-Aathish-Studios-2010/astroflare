"""Astroflare evidence library.

A small, curated set of sources that the assessment rules cite. Nothing here is generated: each source's
bibliographic fields come from the publisher's own record (NASA NTRS, or the PDF itself), each claim paraphrases
what that document (or its abstract) says, and `review.depth` records how much of it was actually read.

What this module guarantees: every citation resolves to a real library entry, entries have the fields a reader
needs to find the document, and a live check can confirm the record still exists and still has the same title.
What it does NOT do: judge whether a source is right, or whether it applies to a given spacecraft.
"""
import json
import re
import threading
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIBRARY_PATH = ROOT / "evidence" / "sources.json"
NTRS_API = "https://ntrs.nasa.gov/api/citations/%s"
STALE_YEARS = 10  # purely descriptive: a source older than this is labelled as such, which says nothing about whether it is still right
VERIFY_TIMEOUT = 12
REQUIRED_SOURCE_FIELDS = ("id", "kind", "title", "issuer", "date", "dateKind", "identifier", "url", "verify", "review", "caveats", "claims")
REVIEW_DEPTHS = ("full text", "abstract")
_ID_RE = re.compile(r"^S\d{2}$")
_CLAIM_RE = re.compile(r"^S\d{2}\.c\d+$")


def load_library(path=None):
    with open(path or LIBRARY_PATH, encoding="utf-8") as f:
        return json.load(f)


def validate_library(lib):
    """Return a list of human-readable problems (empty list = structurally sound). Structure only, not correctness."""
    problems = []
    if not isinstance(lib, dict) or not isinstance(lib.get("sources"), list) or not lib["sources"]:
        return ["library has no sources"]
    seen_ids, seen_claims, seen_urls = set(), set(), set()
    for s in lib["sources"]:
        sid = s.get("id", "?")
        for f in REQUIRED_SOURCE_FIELDS:
            if f not in s:
                problems.append("%s: missing field %s" % (sid, f))
        if not _ID_RE.match(str(sid)):
            problems.append("%s: id must look like S01" % sid)
        if sid in seen_ids:
            problems.append("%s: duplicate source id" % sid)
        seen_ids.add(sid)
        url = str(s.get("url", ""))
        if not url.startswith("https://"):
            problems.append("%s: url must be https" % sid)
        if url in seen_urls:
            problems.append("%s: duplicate url" % sid)
        seen_urls.add(url)
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(s.get("date", ""))):
            problems.append("%s: date must be YYYY-MM-DD" % sid)
        if not str(s.get("title", "")).strip():
            problems.append("%s: empty title" % sid)
        depth = (s.get("review") or {}).get("depth")
        if depth not in REVIEW_DEPTHS:
            problems.append("%s: review.depth must be one of %s" % (sid, REVIEW_DEPTHS))
        if depth == "abstract" and not any("abstract" in str(c).lower() for c in s.get("caveats", [])):
            problems.append("%s: abstract-only sources must say so in their caveats" % sid)
        v = s.get("verify") or {}
        if v.get("method") == "ntrs" and not (v.get("ntrsId") and v.get("expectedTitle")):
            problems.append("%s: ntrs verification needs ntrsId and expectedTitle" % sid)
        if v.get("method") not in ("ntrs", "http"):
            problems.append("%s: unknown verify.method" % sid)
        if not s.get("claims"):
            problems.append("%s: no claims" % sid)
        for c in s.get("claims", []):
            cid = c.get("id", "?")
            if not _CLAIM_RE.match(str(cid)) or not str(cid).startswith(str(sid) + "."):
                problems.append("%s: claim id %s doesn't belong to this source" % (sid, cid))
            if cid in seen_claims:
                problems.append("%s: duplicate claim id" % cid)
            seen_claims.add(cid)
            if len(str(c.get("text", "")).strip()) < 40:
                problems.append("%s: claim text is too short to be a specific statement" % cid)
            if not c.get("topic"):
                problems.append("%s: claim has no topic" % cid)
    for t in lib.get("tensions", []):
        for cid in t.get("claims", []):
            if cid not in seen_claims:
                problems.append("tension %s references unknown claim %s" % (t.get("id"), cid))
        if len(t.get("claims", [])) < 2:
            problems.append("tension %s needs at least two claims" % t.get("id"))
        if not str(t.get("note", "")).strip():
            problems.append("tension %s has no explanatory note" % t.get("id"))
    return problems


class Evidence:
    """Index over a validated library, plus the cached result of the last live verification."""

    def __init__(self, lib=None):
        self.lib = lib if lib is not None else load_library()
        self.sources = {s["id"]: s for s in self.lib["sources"]}
        self.claims = {}
        for s in self.lib["sources"]:
            for c in s["claims"]:
                self.claims[c["id"]] = dict(c, source_id=s["id"])
        self.tensions = self.lib.get("tensions", [])
        self._verification = {}  # source id -> {"status", "checkedAt", "detail"}
        self._lock = threading.Lock()

    # ---------------------------------------------------------------- citing
    def cite(self, claim_ids, today=None):
        """Resolve claim ids into de-duplicated sources and claims (order of first use is kept).
        Unknown ids are returned in `unknown` and never invented around."""
        today = today or date.today()
        order, seen, unknown, claims = [], set(), [], []
        for cid in claim_ids:
            if cid in seen:
                continue  # duplicate citation of the same statement
            seen.add(cid)
            c = self.claims.get(cid)
            if c is None:
                unknown.append(cid)
                continue
            claims.append(c)
            if c["source_id"] not in order:
                order.append(c["source_id"])
        sources = [self.public_source(sid, [c for c in claims if c["source_id"] == sid], today) for sid in order]
        tensions = [t for t in self.tensions if sum(1 for cid in t["claims"] if cid in seen) >= 2]
        return {"sources": sources, "claims": claims, "unknown": unknown, "tensions": tensions}

    def public_source(self, sid, claims=None, today=None):
        s = self.sources[sid]
        today = today or date.today()
        years = age_years(s["date"], today)
        out = {k: s[k] for k in ("id", "kind", "title", "authors", "issuer", "date", "dateKind", "identifier", "url", "caveats")}
        out["review"] = dict(s["review"])
        out["ageYears"] = years
        out["olderThanYears"] = STALE_YEARS if years is not None and years >= STALE_YEARS else None
        out["verification"] = self.verification_for(sid)
        out["claims"] = [{"id": c["id"], "topic": c["topic"], "text": c["text"]} for c in (claims if claims is not None else s["claims"])]
        return out

    def all_sources(self, today=None):
        return [self.public_source(sid, None, today) for sid in self.sources]

    # ---------------------------------------------------------------- live verification
    def verification_for(self, sid):
        with self._lock:
            v = self._verification.get(sid)
        return dict(v) if v else {"status": "not_checked", "checkedAt": None, "detail": "Not checked in this session."}

    def verification_summary(self):
        with self._lock:
            vals = list(self._verification.values())
        stamps = [v["checkedAt"] for v in vals if v.get("checkedAt")]
        return {"checked": len(vals), "total": len(self.sources), "lastChecked": max(stamps) if stamps else None,
                "verified": sum(1 for v in vals if v["status"] == "verified"),
                "problems": sum(1 for v in vals if v["status"] not in ("verified", "not_checked"))}

    def verify_all(self, opener=None):
        """Check each source against its publisher's record. Statuses: verified | title_mismatch | unreachable.
        This confirms the record exists and the title is unchanged; it does NOT re-read the content."""
        opener = opener or urllib.request.urlopen
        results = {}
        for sid, s in self.sources.items():
            results[sid] = verify_one(s, opener)
        with self._lock:
            self._verification.update(results)
        return self.verification_summary()


def age_years(date_str, today):
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None
    years = today.year - d.year - ((today.month, today.day) < (d.month, d.day))  # whole calendar years, no leap-day drift
    return max(0, years)


def _norm_title(t):
    return re.sub(r"\s+", " ", str(t or "")).strip().lower()


def verify_one(source, opener):
    v = source["verify"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        if v["method"] == "ntrs":
            req = urllib.request.Request(NTRS_API % v["ntrsId"], headers={"Accept": "application/json"})
            with opener(req, timeout=VERIFY_TIMEOUT) as r:
                record = json.loads(r.read(2_000_000))
            title = record.get("title") if isinstance(record, dict) else None
            if _norm_title(title) == _norm_title(v["expectedTitle"]):
                return {"status": "verified", "checkedAt": now, "detail": "Record found at NASA NTRS with the expected title."}
            return {"status": "title_mismatch", "checkedAt": now, "detail": "A record exists at NASA NTRS but its title differs from the one reviewed."}
        req = urllib.request.Request(source["url"], method="HEAD")
        with opener(req, timeout=VERIFY_TIMEOUT) as r:
            ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower() if getattr(r, "headers", None) else ""
        expected = v.get("expectedContentType")
        if expected and ctype and ctype != expected:
            return {"status": "title_mismatch", "checkedAt": now, "detail": "The link answered but with a different document type than expected."}
        return {"status": "verified", "checkedAt": now, "detail": "The link answered; the document content was not re-read."}
    except Exception as e:  # network errors, HTTP errors, bad JSON: all mean "could not confirm"
        code = getattr(e, "code", None)
        return {"status": "unreachable", "checkedAt": now, "detail": "Could not confirm the source (%s)." % ("HTTP %s" % code if code else "no usable response")}


_default = None
_default_lock = threading.Lock()


def default_evidence():
    """Process-wide instance (loads and validates the shipped library once)."""
    global _default
    with _default_lock:
        if _default is None:
            lib = load_library()
            problems = validate_library(lib)
            if problems:
                raise RuntimeError("evidence library is invalid: " + "; ".join(problems[:3]))
            _default = Evidence(lib)
        return _default
