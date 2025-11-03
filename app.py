import os
from urllib.parse import quote
import requests
from flask import Flask, jsonify, Response

APP_NAME = "roproxy-gamepasses-py"
R_GAMES = "https://games.roproxy.com/v2/users/{user_id}/games?accessFilter=Public&limit=50&sortOrder=Asc"
R_PASSES = "https://apis.roproxy.com/game-passes/v1/universes/{universe_id}/game-passes?pageSize=100&passView=Full"

DEFAULT_TIMEOUT = (5, 20)
UA = {"User-Agent": f"{APP_NAME}/1.0"}

session = requests.Session()
session.headers.update(UA)

app = Flask(__name__)

def http_get_json(url):
    r = session.get(url, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()

def fetch_universe_ids(user_id):
    data = http_get_json(R_GAMES.format(user_id=user_id))
    items = data.get("data") or []
    return [item["id"] for item in items if isinstance(item, dict) and "id" in item]

def fetch_passes_for_universe(universe_id):
    data = http_get_json(R_PASSES.format(universe_id=universe_id))
    items = data.get("data") or []
    out = []
    for p in items:
        pid = p.get("id")
        name = p.get("name") or ""
        price = p.get("price")
        link = None
        if pid:
            slug = quote(name) if name else "Gamepass"
            link = f"https://www.roblox.com/game-pass/{pid}/{slug}"
        out.append({
            "universeId": universe_id,
            "id": pid,
            "name": name,
            "price": price,
            "productId": p.get("productId"),
            "link": link
        })
    return out

@app.get("/healthz")
def healthz():
    return jsonify({"ok": True})

@app.get("/user/<user_id>/gamepasses")
def user_gamepasses(user_id):
    try:
        universes = fetch_universe_ids(user_id)
        passes = []
        for u in universes:
            try:
                passes.extend(fetch_passes_for_universe(u))
            except requests.HTTPError as e:
                code = e.response.status_code if e.response is not None else "unknown"
                passes.append({"universeId": u, "error": f"universe_fetch_failed:{code}"})
        total = sum(1 for p in passes if isinstance(p, dict) and p.get("id"))
        return jsonify({"userId": user_id, "universes": universes, "total": total, "passes": passes})
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else 502
        return jsonify({"error": f"http_error:{code}"}), 502
    except requests.RequestException as e:
        return jsonify({"error": f"request_exception:{str(e)}"}), 502

@app.get("/user/<user_id>/gamepasses.html")
def user_gamepasses_html(user_id):
    try:
        universes = fetch_universe_ids(user_id)
        rows = []
        for u in universes:
            try:
                rows.extend(fetch_passes_for_universe(u))
            except requests.HTTPError:
                rows.append({"universeId": u, "id": None, "name": None, "price": None, "link": None})
        html = [
            "<!doctype html><html><head><meta charset='utf-8'><title>Gamepasses</title>",
            "<meta name='viewport' content='width=device-width,initial-scale=1'>",
            "<style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Arial,sans-serif;padding:24px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px}th{background:#f5f5f5;text-align:left}</style>",
            "</head><body>",
            "<h1>Gamepasses for {}</h1>".format(user_id),
            "<table><thead><tr><th>Universe ID</th><th>Pass ID</th><th>Name</th><th>Price</th><th>Link</th></tr></thead><tbody>"
        ]
        for p in rows:
            link_cell = ""
            if p.get("link"):
                link_cell = '<a href="{}" target="_blank" rel="noopener">open</a>'.format(p.get("link"))
            html.append(
                "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                    p.get("universeId"),
                    p.get("id") or "",
                    p.get("name") or "",
                    "" if p.get("price") is None else p.get("price"),
                    link_cell
                )
            )
        html.append("</tbody></table></body></html>")
        return Response("\n".join(html), mimetype="text/html")
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else 502
        return Response("HTTP error {}".format(code), status=502, mimetype="text/plain")
    except requests.RequestException as e:
        return Response("Request error: {}".format(str(e)), status=502, mimetype="text/plain")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
