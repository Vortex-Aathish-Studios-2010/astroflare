"""Start the whole AstroFlare stack in one container (Render free plan; see ../Dockerfile and ../render.yaml).

    python engine/render_start.py

Three programs, one public port:

  FreeLLMAPI   the AI router, 127.0.0.1:3001, private
  engine       the Python assessment engine (engine/server.py), 127.0.0.1:8001, private
  site         the AstroFlare interface (server.mjs), on Render's $PORT; it relays /api/* to the engine

Render's free plan keeps no files between restarts, so FreeLLMAPI starts with an empty database every time and
creates a new random unified key ("freellmapi-..."). Its provider keys come back from FREEAPI_CONFIG_JSON (a secret set
in the Render dashboard); this script reads the new unified key from FreeLLMAPI's own database and hands it only to the
engine. Visitors reach the site only: the router and the engine are never exposed. Key values are never printed.
"""
import os
import secrets
import signal
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
ROOT = ENGINE_DIR.parent
ROUTER_DIR = Path(os.environ.get("FREELLMAPI_DIR") or "/opt/freellmapi")
ROUTER_PORT = 3001
ENGINE_PORT = 8001
ROUTER_DB = os.environ.get("FREEAPI_DB_PATH") or "/data/freellmapi.db"
# The router's key is handed to the engine through this file (owner-only), so the engine and the site can start at
# once instead of waiting for the router; AI becomes available as soon as the file appears.
KEY_FILE = os.environ.get("FREELLMAPI_KEY_FILE") or "/data/router.key"
ROUTER_START_TIMEOUT = 120  # seconds; first boot runs migrations and a catalog sync
ENGINE_START_TIMEOUT = 30
RESTARTS = 5
# Only FreeLLMAPI needs these; neither the engine nor the site ever sees them.
ROUTER_ONLY = ("ENCRYPTION_KEY", "FREEAPI_CONFIG_JSON", "FREEAPI_CONFIG_PATH", "FREEAPI_DB_PATH")
# Only the engine talks to an AI service.
ENGINE_ONLY = ("FREELLMAPI_API_KEY", "FREELLMAPI_BASE_URL", "FREELLMAPI_MODEL", "AI_PROVIDER", "ANTHROPIC_API_KEY", "GEMINI_API_KEY")


def log(message):
    print("[render_start] " + message, flush=True)


def router_env(base):
    """FreeLLMAPI's environment: loopback only, fixed port, a database path, and an encryption key. The key only
    protects a database that disappears with the container, so a fresh one per start is fine when none is set."""
    env = {k: v for k, v in base.items() if k != "PORT"}  # Render's PORT belongs to the site
    env.update(PORT=str(ROUTER_PORT), HOST="127.0.0.1", NODE_ENV="production", FREEAPI_DB_PATH=ROUTER_DB,
               FREELLMAPI_UPDATE_CHECK="off", FREEAPI_BLOCK_PRIVATE_PROVIDER_URLS="true")
    env.setdefault("NODE_OPTIONS", "--max-old-space-size=256")  # the free plan has 512 MB for everything
    if not env.get("ENCRYPTION_KEY"):
        env["ENCRYPTION_KEY"] = secrets.token_hex(32)
    return env


def astroflare_env(base, unified_key, key_file=None):
    """The engine's environment: private on 127.0.0.1:8001, the local router and its key (or the file that will
    hold it), no router secrets."""
    env = {k: v for k, v in base.items() if k not in ROUTER_ONLY and k != "NODE_OPTIONS"}
    env.setdefault("AI_PROVIDER", "freellmapi")
    env.update(PORT=str(ENGINE_PORT), ASTROFLARE_HOST="127.0.0.1", ASTROFLARE_ENV="production",
               FREELLMAPI_BASE_URL="http://127.0.0.1:%d/v1" % ROUTER_PORT)
    if unified_key:
        env["FREELLMAPI_API_KEY"] = unified_key
    elif key_file:
        env["FREELLMAPI_API_KEY_FILE"] = key_file
    return env


def write_key_file(key, path=None):
    """Write the router key for the engine: owner-only permissions, replaced atomically so a reader never sees half."""
    path = Path(path or KEY_FILE)
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(key)
    os.replace(str(tmp), str(path))


def site_env(base):
    """The public site's environment: Render's PORT, the engine as its upstream, and no secrets of any kind."""
    env = {k: v for k, v in base.items() if k not in ROUTER_ONLY + ENGINE_ONLY}
    env["ASTROFLARE_UPSTREAM"] = "http://127.0.0.1:%d" % ENGINE_PORT
    env["NODE_OPTIONS"] = "--max-old-space-size=96"
    return env


def read_unified_key(db_path):
    """The router's unified key from its settings table, or None if the database or the row isn't there yet."""
    if not Path(db_path).is_file():
        return None
    try:
        con = sqlite3.connect("file:%s?mode=ro" % Path(db_path).as_posix(), uri=True, timeout=5)
        try:
            row = con.execute("SELECT value FROM settings WHERE key = 'unified_api_key'").fetchone()
        finally:
            con.close()
    except sqlite3.Error:
        return None
    value = row[0] if row else None
    return value if isinstance(value, str) and value.startswith("freellmapi-") else None


def _answers(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def router_ready():
    return _answers("http://127.0.0.1:%d/api/ping" % ROUTER_PORT)


def engine_ready():
    return _answers("http://127.0.0.1:%d/healthz" % ENGINE_PORT)


def start_router():
    return subprocess.Popen(["node", "server/dist/index.js"], cwd=ROUTER_DIR, env=router_env(os.environ))


def start_engine():
    return subprocess.Popen([sys.executable, str(ENGINE_DIR / "server.py")], cwd=ENGINE_DIR, env=astroflare_env(os.environ, None, KEY_FILE))


def start_site():
    return subprocess.Popen(["node", "server.mjs"], cwd=ROOT, env=site_env(os.environ))


def wait_for(proc, ready, timeout):
    """True once ready() answers; False if the process exits or the time runs out."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        if ready():
            return True
        time.sleep(1)
    return False


def main():
    """Start everything at once so a waking free-plan service answers quickly: the site and the engine come up in
    seconds, while the router boots in parallel and AI is enabled when its key is ready."""
    try:
        os.remove(KEY_FILE)  # a key from an earlier router run is never valid for this one
    except OSError:
        pass
    router = start_router()
    engine = start_engine()
    if not wait_for(engine, engine_ready, ENGINE_START_TIMEOUT):
        log("The assessment engine did not start; stopping.")
        for p in (engine, router):
            if p.poll() is None:
                p.terminate()
        return 1
    site = start_site()
    log("Site and engine are up; waiting for FreeLLMAPI before enabling AI explanations.")
    stopping = []

    def stop(*_):
        stopping.append(True)  # tell the loop below not to restart anything
        for p in (site, engine, router):
            if p.poll() is None:
                p.terminate()
    signal.signal(signal.SIGTERM, stop)

    key, router_deadline = None, time.monotonic() + ROUTER_START_TIMEOUT
    restarts = {"router": 0, "engine": 0}
    while site.poll() is None and not stopping:
        time.sleep(1)
        if key is None and router.poll() is None and router_ready():
            key = read_unified_key(ROUTER_DB)
            if key:
                write_key_file(key)
                log("FreeLLMAPI is ready; AI explanations are enabled.")
        if key is None and time.monotonic() > router_deadline and router_deadline:
            log("FreeLLMAPI did not become ready; the site runs without AI explanations.")
            router_deadline = 0
        if stopping:
            break
        # The database survives a router crash inside the same container, so the key file stays valid.
        if router.poll() is not None and restarts["router"] < RESTARTS:
            restarts["router"] += 1
            log("FreeLLMAPI stopped (exit %s); restarting (%d/%d)." % (router.returncode, restarts["router"], RESTARTS))
            router = start_router()
        if engine.poll() is not None and restarts["engine"] < RESTARTS:
            restarts["engine"] += 1
            log("The assessment engine stopped (exit %s); restarting (%d/%d)." % (engine.returncode, restarts["engine"], RESTARTS))
            engine = start_engine()
    stop()
    return site.returncode or 0


if __name__ == "__main__":
    sys.exit(main())
