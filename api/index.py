from __future__ import annotations

import base64
import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SRC = PROJECT_ROOT / "src" / "python"
sys.path.insert(0, str(PYTHON_SRC))

from agent import crear_agente
from image_utils import describir_imagen_bytes


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        self._send_json(
            200,
            {
                "ok": True,
                "message": "API lista. Envia POST /api con image_base64 y media_type.",
            },
        )

    def do_POST(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body or b"{}")

            image_base64 = payload.get("image_base64")
            if not image_base64:
                self._send_json(400, {"error": "Falta image_base64 en el cuerpo JSON."})
                return

            image_bytes = base64.b64decode(image_base64)
            media_type = payload.get("media_type", "image/png")

            agent = crear_agente()
            result = describir_imagen_bytes(agent, image_bytes, media_type)
            self._send_json(200, result.model_dump())
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
