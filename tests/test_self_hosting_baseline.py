import contextlib
import json
import os
import socket
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_API = ROOT / "docker" / "api" / "bootstrap-api.py"
SEMANTIC_DISCLAIMER = "Semantic search is textual similarity, not tafsir, fatwa, or religious ruling."
REQUIRED_FILES = [
    ".env.example",
    ".env.api.example",
    ".env.cli.example",
    ".env.web.example",
    "compose.yaml",
    "docker/api.Dockerfile",
    "docker/web.Dockerfile",
    "docs/self-hosting.md",
    "docs/testing.md",
    "docs/religious-safety.md",
    "docs/api.md",
    "docs/cli.md",
    "docs/release-readiness.md",
    "scripts/run-repository-tests.sh",
]


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def load_json(url):
    with urllib.request.urlopen(url, timeout=1) as response:
        return json.loads(response.read().decode("utf-8"))


@contextlib.contextmanager
def running_bootstrap_api():
    port = find_free_port()
    env = os.environ.copy()
    env.update(
        {
            "QURANKIT_APP_NAME": "QuranKit API Bootstrap Test",
            "QURANKIT_BIND_HOST": "127.0.0.1",
            "QURANKIT_BIND_PORT": str(port),
            "QURANKIT_DATABASE_URL": "postgresql://qurankit:super-secret-password@db:5432/qurankit",
            "QURANKIT_PRIVACY_MODE": "private-by-default",
            "QURANKIT_SOURCE_ATTRIBUTION_REQUIRED": "true",
            "QURANKIT_SEMANTIC_SEARCH_DISCLAIMER": SEMANTIC_DISCLAIMER,
        }
    )

    process = subprocess.Popen(
        [sys.executable, str(BOOTSTRAP_API)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        base_url = f"http://127.0.0.1:{port}"

        for _ in range(40):
            try:
                load_json(f"{base_url}/health")
                break
            except urllib.error.URLError:
                time.sleep(0.1)
        else:
            raise AssertionError("Bootstrap API did not become ready in time.")

        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


class SelfHostingBaselineTests(unittest.TestCase):
    def test_required_files_exist(self):
        missing = [
            relative_path
            for relative_path in REQUIRED_FILES
            if not (ROOT / relative_path).is_file()
        ]
        self.assertEqual([], missing)

    def test_compose_and_cli_env_preserve_privacy_guardrails(self):
        compose_text = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        cli_env_text = (ROOT / ".env.cli.example").read_text(encoding="utf-8")
        self_hosting_text = (ROOT / "docs" / "self-hosting.md").read_text(encoding="utf-8")

        self.assertIn("profiles:", compose_text)
        self.assertIn("semantic-search", compose_text)
        self.assertIn("QURANKIT_PRIVACY_MODE", compose_text)
        self.assertIn("QURANKIT_CLI_PRIVACY_MODE=private-by-default", cli_env_text)
        self.assertIn(
            "QURANKIT_CLI_SEMANTIC_SEARCH_DISCLAIMER=Semantic search is textual similarity, not tafsir, fatwa, or religious ruling.",
            cli_env_text,
        )
        self.assertIn(".env.cli.example", self_hosting_text)

    def test_bootstrap_api_reports_guardrails_without_exposing_database_credentials(self):
        with running_bootstrap_api() as base_url:
            root_payload = load_json(f"{base_url}/")
            health_payload = load_json(f"{base_url}/health")

        serialized_root = json.dumps(root_payload, sort_keys=True)

        self.assertEqual("ok", health_payload["status"])
        self.assertEqual("QuranKit API Bootstrap Test", health_payload["service"])
        self.assertEqual("private-by-default", health_payload["privacyMode"])
        self.assertTrue(health_payload["sourceAttributionRequired"])

        self.assertEqual("bootstrap", root_payload["status"])
        self.assertEqual("QuranKit API Bootstrap Test", root_payload["name"])
        self.assertEqual("QuranKit bootstrap API is running.", root_payload["message"])
        self.assertNotIn("databaseUrl", root_payload)
        self.assertNotIn("super-secret-password", serialized_root)
        self.assertTrue(root_payload["database"]["configured"])
        self.assertEqual("postgresql", root_payload["database"]["driver"])
        self.assertTrue(root_payload["safety"]["sourceAttributionRequired"])
        self.assertEqual("private-by-default", root_payload["safety"]["privacyMode"])
        self.assertEqual(
            SEMANTIC_DISCLAIMER,
            root_payload["safety"]["semanticSearchDisclaimer"],
        )
