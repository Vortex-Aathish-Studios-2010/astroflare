"""Check your real API setup without exposing any key.

    python check_keys.py

Runs live checks and prints PASS / FAIL with a plain-English reason. Key values are never printed.
It checks the AI service chosen by AI_PROVIDER in your .env (default: anthropic):

  anthropic   1. key + model (free): lists the models your key can use and confirms ANTHROPIC_MODEL is one.
              2. one tiny real message (a few tokens, a fraction of a cent).
  freellmapi  1. router reachable and key accepted (free): lists the router's models. If nothing answers on the
                 configured port, it looks for the app on the usual ports and tells you the right URL.
              2. your FREELLMAPI_MODEL choice(s) exist in that list (free).
              3. one tiny real chat message through the router (uses a little of a free-tier quota). Note that the
                 router's 'available' flag only means it holds a key for that provider; this real message is the
                 only proof that your account can actually use the model.

Then it checks NASA DONKI: the last 30 days of solar flares from NASA's official service (no key needed).
"""
import json
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit

import server


def step(label, fn):
    print("%-34s" % label, end=" ", flush=True)
    try:
        note = fn()
        print("PASS" + (" (%s)" % note if note else ""))
        return True
    except server.ApiError as e:
        print("FAIL\n   " + e.message)
        return False


def check_model_listed():
    models = server.list_models()
    wanted = server.model_name()
    match = [m for m in models if m["id"] == wanted]
    if not match:
        available = ", ".join(sorted(m["id"] for m in models if m["lifecycle"] == "active")[:8])
        raise server.ApiError(0, "model_unknown", "Your key works, but model '%s' isn't available to it. Remove ANTHROPIC_MODEL from .env "
                              "to use the default (%s), or pick one of: %s" % (wanted, server.DEFAULT_MODEL, available or "none listed"))
    if match[0]["lifecycle"] != "active":
        raise server.ApiError(0, "model_old", "Model '%s' is %s. Choose a current model (default: %s)." % (wanted, match[0]["lifecycle"], server.DEFAULT_MODEL))
    return "key accepted; model %s is %s" % (wanted, match[0]["lifecycle"])


def check_message():
    r = server.call_anthropic("Reply with the single word OK.", system="Reply with the single word OK.", max_tokens=64, allow_empty=True)
    return "model %s answered" % r["model"]


def check_router_listed():
    catalog = server.freellm_model_catalog()
    base = server.freellm_base()[0]
    if catalog is None:
        return "router reachable at %s, key accepted (model list not in a recognised format)" % base
    return "router reachable at %s, key accepted; %d models listed" % (base, len(catalog))


def find_other_router_port():
    """Look for an OpenAI-style service (the FreeLLMAPI app) on the usual ports, other than the configured one."""
    configured = urlsplit(server.freellm_base()[0] or "").port
    ports = []
    for port in (server.desktop_router_port(), 31415, 3001):
        if port and port not in ports and port != configured:
            ports.append(port)
    for port in ports:
        req = urllib.request.Request("http://127.0.0.1:%d/v1/models" % port, headers={"Accept": "application/json"})
        try:
            with server._urlopen(req, timeout=2):
                return port
        except urllib.error.HTTPError as e:
            try:
                if e.code == 401 and json.loads(e.read(2000))["error"]["type"] == "authentication_error":
                    return port
            except Exception:
                pass
        except Exception:
            continue
    return None


def check_models_exist():
    catalog = server.freellm_model_catalog()
    if catalog is None:
        return "router didn't list its models in a recognised format; the message check below will tell"
    known = {m["id"]: m for m in catalog}
    notes = []
    for model in server.freellm_models():
        if model == "auto" or model.startswith("auto:"):
            notes.append("%s (router chooses; can be slow if it tries retired models first)" % model)
        elif model not in known:
            examples = ", ".join(sorted(m["id"] for m in catalog if m["available"])[:6])
            raise server.ApiError(0, "model_unknown", "Model '%s' isn't in the router's list. Models it lists as available include: %s" % (model, examples or "none"))
        elif not known[model]["available"]:
            raise server.ApiError(0, "model_unavailable", "Model '%s' is listed but unavailable (%s). Add the provider's key in FreeLLMAPI or choose another model." % (model, known[model]["reason"] or "no reason given"))
        else:
            notes.append("%s listed" % model)
    return "; ".join(notes)


def check_router_message():
    r = server.call_freellmapi("Reply with the single word OK.", system="Reply with the single word OK.", max_tokens=64, allow_empty=True)
    return "answered by %s" % (r["routedVia"] or r["model"])


def check_nasa():
    d = server.fetch_flares()
    return "%d flares in the last %d days from %s%s" % (len(d["flares"]), d["windowDays"], d["host"], ", key: %s" % d["keyUsed"] if d["keyUsed"] != "none" else ", no key needed")


def main():
    server.load_env()
    s = server.status_payload()
    ai = s["ai"]
    print("AI brief: [%s] %s" % (ai["label"], ai["message"]))
    print("NASA:     ", s["nasa"]["message"])
    print()
    results = []
    if ai["ready"] and ai["provider"] == "freellmapi":
        listed = step("FreeLLMAPI router + key (free)", check_router_listed)
        results.append(listed)
        if listed:
            results.append(step("FreeLLMAPI model(s) listed", check_models_exist))
            results.append(step("FreeLLMAPI message", check_router_message))
        else:
            port = find_other_router_port()
            if port:
                print("   An OpenAI-style service IS answering on port %d. If that is FreeLLMAPI, set "
                      "FREELLMAPI_BASE_URL=http://127.0.0.1:%d/v1 in .env and restart." % (port, port))
            for label in ("FreeLLMAPI model(s) listed", "FreeLLMAPI message"):
                print("%-34s skipped (router check failed)" % label)
            results.append(False)
    elif ai["ready"]:
        listed = step("Anthropic key + model (free)", check_model_listed)
        results.append(listed)
        results.append(step("Anthropic message (few tokens)", check_message))
    else:
        print("AI checks skipped: the AI service isn't set up yet (see the message above).")
        results.append(False)
    results.append(step("NASA DONKI solar flares", check_nasa))
    failed = results.count(False)
    print("\nAll checks passed." if not failed else "\n%d check(s) failed. See README.md > Troubleshooting." % failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
