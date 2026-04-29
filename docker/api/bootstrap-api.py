import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


APP_NAME = os.getenv("QURANKIT_APP_NAME", "QuranKit API Bootstrap")
BIND_HOST = os.getenv("QURANKIT_BIND_HOST", "0.0.0.0")
BIND_PORT = int(os.getenv("QURANKIT_BIND_PORT", "8000"))
DATABASE_URL = os.getenv("QURANKIT_DATABASE_URL", "postgresql://qurankit:qurankit@db:5432/qurankit")
PRIVACY_MODE = os.getenv("QURANKIT_PRIVACY_MODE", "private-by-default")
ATTRIBUTION_REQUIRED = os.getenv("QURANKIT_SOURCE_ATTRIBUTION_REQUIRED", "true").lower() == "true"
SEMANTIC_SEARCH_DISCLAIMER = os.getenv(
    "QURANKIT_SEMANTIC_SEARCH_DISCLAIMER",
    "Semantic search is textual similarity, not tafsir, fatwa, or religious ruling.",
)


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": APP_NAME,
                    "privacyMode": PRIVACY_MODE,
                    "sourceAttributionRequired": ATTRIBUTION_REQUIRED,
                },
            )
            return

        if self.path == "/":
            self._send_json(
                200,
                {
                    "name": APP_NAME,
                    "status": "bootstrap",
                    "message": "QuranKit bootstrap API is running.",
                    "databaseUrl": DATABASE_URL,
                    "safety": {
                        "sourceAttributionRequired": ATTRIBUTION_REQUIRED,
                        "semanticSearchDisclaimer": SEMANTIC_SEARCH_DISCLAIMER,
                        "privacyMode": PRIVACY_MODE,
                    },
                },
            )
            return

        self._send_json(
            404,
            {
                "status": "not_found",
                "message": "Available routes: / and /health",
            },
        )

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer((BIND_HOST, BIND_PORT), Handler)
    server.serve_forever()
