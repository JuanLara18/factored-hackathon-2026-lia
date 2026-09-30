"""Emula Firebase Hosting de firebase.json (cleanUrls, sin barra final, CSP) para probar el sitio del arbol de trabajo."""

from __future__ import annotations

import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SITIO = RAIZ / "tecnologia" / "web" / "sitio"
CABECERAS = {
    h["key"]: h["value"]
    for regla in json.loads((RAIZ / "firebase.json").read_text())["hosting"]["headers"]
    if regla["source"] == "**"
    for h in regla["headers"]
}


class Manejador(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k) -> None:
        super().__init__(*a, directory=str(SITIO), **k)

    def log_message(self, *a) -> None:  # silencio
        pass

    def _ir(self, destino: str) -> None:
        self.send_response(301)
        self.send_header("Location", destino)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        ruta, _, consulta = self.path.partition("?")
        q = "?" + consulta if consulta else ""
        if ruta.endswith("/index.html"):
            return self._ir((ruta[: -len("/index.html")] or "/") + q)
        if ruta.endswith(".html"):
            return self._ir(ruta[:-5] + q)
        if ruta != "/" and ruta.endswith("/"):
            return self._ir(ruta.rstrip("/") + q)
        rel = ruta.lstrip("/")
        if rel and not (SITIO / rel).is_file():
            if (SITIO / (rel + ".html")).is_file():
                self.path = "/" + rel + ".html" + q
            elif (SITIO / rel / "index.html").is_file():
                self.path = "/" + rel + "/index.html" + q
        super().do_GET()

    def end_headers(self) -> None:
        for k, v in CABECERAS.items():
            self.send_header(k, v)
        super().end_headers()


def arrancar(puerto: int = 5000) -> ThreadingHTTPServer:
    srv = ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
