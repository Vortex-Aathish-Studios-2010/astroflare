"""Tests for render_start.py, the container launcher that runs FreeLLMAPI, the engine and the site together."""
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

import render_start

KEY = "freellmapi-" + "ab" * 24


class UnifiedKey(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.db = str(Path(self.dir) / "freellmapi.db")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def make_db(self, rows):
        con = sqlite3.connect(self.db)
        con.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT)")
        con.executemany("INSERT INTO settings VALUES (?, ?)", rows)
        con.commit()
        con.close()

    def test_reads_the_key_the_router_generated(self):
        self.make_db([("routing_strategy", "balanced"), ("unified_api_key", KEY)])
        self.assertEqual(render_start.read_unified_key(self.db), KEY)

    def test_missing_database_table_or_row_gives_none(self):
        self.assertIsNone(render_start.read_unified_key(self.db))
        Path(self.db).write_bytes(b"")
        self.assertIsNone(render_start.read_unified_key(self.db))
        Path(self.db).unlink()
        self.make_db([("routing_strategy", "balanced")])
        self.assertIsNone(render_start.read_unified_key(self.db))

    def test_value_that_is_not_a_unified_key_is_ignored(self):
        self.make_db([("unified_api_key", "something-else")])
        self.assertIsNone(render_start.read_unified_key(self.db))

    def test_read_is_read_only(self):
        self.make_db([("unified_api_key", KEY)])
        before = Path(self.db).read_bytes()
        render_start.read_unified_key(self.db)
        self.assertEqual(Path(self.db).read_bytes(), before)


class Environments(unittest.TestCase):
    BASE = {"PORT": "10000", "RENDER": "true", "ASTROFLARE_ENV": "production", "FREEAPI_CONFIG_JSON": '{"keys":[]}',
            "ENCRYPTION_KEY": "e" * 64, "FREELLMAPI_MODEL": "gemini-3.5-flash", "ANTHROPIC_API_KEY": "sk-ant-x" * 5, "PATH": "/usr/bin"}

    def test_router_is_private_and_off_the_platform_port(self):
        env = render_start.router_env(self.BASE)
        self.assertEqual((env["PORT"], env["HOST"]), ("3001", "127.0.0.1"))
        self.assertEqual(env["FREEAPI_CONFIG_JSON"], '{"keys":[]}')
        self.assertEqual(env["ENCRYPTION_KEY"], "e" * 64)
        self.assertEqual(env["FREEAPI_DB_PATH"], render_start.ROUTER_DB)

    def test_router_gets_a_random_encryption_key_when_none_is_set(self):
        base = {k: v for k, v in self.BASE.items() if k != "ENCRYPTION_KEY"}
        a, b = render_start.router_env(base)["ENCRYPTION_KEY"], render_start.router_env(base)["ENCRYPTION_KEY"]
        self.assertEqual(len(a), 64)
        self.assertNotEqual(a, b)

    def test_engine_is_private_gets_the_key_and_local_router_but_no_router_secrets(self):
        env = render_start.astroflare_env(self.BASE, KEY)
        self.assertEqual((env["PORT"], env["ASTROFLARE_HOST"], env["ASTROFLARE_ENV"]), ("8001", "127.0.0.1", "production"))
        self.assertEqual((env["AI_PROVIDER"], env["FREELLMAPI_API_KEY"]), ("freellmapi", KEY))
        self.assertEqual(env["FREELLMAPI_BASE_URL"], "http://127.0.0.1:3001/v1")
        for name in ("FREEAPI_CONFIG_JSON", "ENCRYPTION_KEY", "FREEAPI_DB_PATH"):
            self.assertNotIn(name, env)

    def test_without_a_key_the_engine_still_starts_without_explanations(self):
        env = render_start.astroflare_env(self.BASE, None)
        self.assertNotIn("FREELLMAPI_API_KEY", env)
        self.assertEqual(env["AI_PROVIDER"], "freellmapi")

    def test_site_gets_the_platform_port_and_the_engine_but_no_secrets(self):
        env = render_start.site_env(dict(self.BASE, FREELLMAPI_API_KEY=KEY))
        self.assertEqual(env["PORT"], "10000")
        self.assertEqual(env["ASTROFLARE_UPSTREAM"], "http://127.0.0.1:8001")
        for name in ("FREEAPI_CONFIG_JSON", "ENCRYPTION_KEY", "FREELLMAPI_API_KEY", "FREELLMAPI_MODEL", "ANTHROPIC_API_KEY", "AI_PROVIDER"):
            self.assertNotIn(name, env)
        self.assertNotIn(KEY, repr(env))

    def test_engine_can_start_before_the_router_and_pick_up_the_key_from_the_file(self):
        import os
        import server
        d = tempfile.mkdtemp()
        key_file = os.path.join(d, "router.key")
        saved = dict(os.environ)
        try:
            os.environ.clear()
            os.environ.update(render_start.astroflare_env(self.BASE, None, key_file))
            self.assertEqual(os.environ["FREELLMAPI_API_KEY_FILE"], key_file)
            self.assertNotIn("FREELLMAPI_API_KEY", os.environ)
            self.assertEqual(server.ai_status()["state"], "missing")  # router not ready yet: the site works, AI is off
            render_start.write_key_file(KEY, key_file)
            self.assertEqual(server.freellm_key(), KEY)
            self.assertEqual(server.ai_status()["state"], "ok")  # no restart needed
            self.assertFalse(os.path.exists(key_file + ".tmp"))
        finally:
            os.environ.clear()
            os.environ.update(saved)
            shutil.rmtree(d, ignore_errors=True)

    def test_a_key_given_directly_wins_over_the_file(self):
        env = render_start.astroflare_env(self.BASE, KEY, "/nonexistent")
        self.assertEqual(env["FREELLMAPI_API_KEY"], KEY)
        self.assertNotIn("FREELLMAPI_API_KEY_FILE", env)

    def test_each_program_gets_its_own_port(self):
        ports = {render_start.ROUTER_PORT, render_start.ENGINE_PORT, 10000}
        self.assertEqual(len(ports), 3)

    def test_engine_settings_are_accepted_by_the_engine(self):
        import os
        import server
        saved = dict(os.environ)
        try:
            os.environ.clear()
            os.environ.update(render_start.astroflare_env(self.BASE, KEY))
            self.assertEqual(server.ai_status()["state"], "ok")
            self.assertEqual(server.bind_host(), "127.0.0.1")
        finally:
            os.environ.clear()
            os.environ.update(saved)


if __name__ == "__main__":
    unittest.main(verbosity=2)
