import os
import logging
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import httpx

# ============================================================
# HNTH SIMPLE UID INFO API
# No Firebase, no login, no dashboard, no /api folder required.
# 1. CORS enabled so any website/app can call this API from a browser
#    (fixes the "blocked by CORS policy" error).
# 2. The API key is never shown in the website's opening response.
# ============================================================

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Allow cross-origin requests from ANY website (fixes the browser
# "blocked by CORS policy" error users were facing).
CORS(app, resources={r"/*": {"origins": "*"}})

UPSTREAM_URL = os.getenv("UPSTREAM_URL", "https://apiv2.mlbbshop.com/ign").strip()

# Browsers must never cache API responses, so users always get fresh data
# and never see an old cached copy of the opening response.
NO_STORE_HEADERS = {"Cache-Control": "no-store"}


def no_store(payload, status=200):
    """JSON response with CORS-friendly no-cache headers."""
    response = make_response(jsonify(payload), status)
    response.headers.update(NO_STORE_HEADERS)
    return response


@app.get("/")
def home():
    """Show API information and available endpoints.

    The API key is intentionally NOT included in this response, so anyone
    opening the website URL never sees it.
    """
    base_url = request.url_root.rstrip("/")
    return no_store({
        "status": "ok",
        "service": "HNTH UID Info API",
        "message": "API is online",
        "base_url": base_url,
        "endpoints": {
            "health": f"{base_url}/api/health",
            "player_lookup": f"{base_url}/api/player"
        }
    })


@app.get("/api/health")
def health():
    """Simple health check that does not require upstream credentials."""
    return no_store({
        "status": "ok",
        "service": "HNTH UID Info API"
    })


@app.get("/api/player")
def player():
    """Look up player information using the key supplied in the URL.

    Example: /api/player?uid=PLAYER_UID&key=YOUR_API_KEY
    No Vercel UPSTREAM_KEY environment variable is required. The supplied
    key is forwarded to the upstream provider as its `key` parameter.
    """
    uid = (request.args.get("uid") or "").strip()
    api_key = (request.args.get("key") or "").strip()
    game = (request.args.get("game") or "freefire2").strip()
    region = (request.args.get("region") or "bd").strip()

    if not api_key:
        return no_store({
            "error": "Missing API key",
            "message": "Add your API key as the 'key' parameter, e.g. ?uid=PLAYER_UID&key=YOUR_API_KEY"
        }, 400)

    if not uid or len(uid) < 4:
        return no_store({
            "error": "Invalid UID",
            "message": "Provide a UID with at least 4 characters."
        }, 400)

    try:
        upstream_response = httpx.get(
            UPSTREAM_URL,
            params={
                "game": game,
                "region": region,
                "key": api_key,
                "user_id": uid
            },
            timeout=15.0
        )
        upstream_response.raise_for_status()
        upstream_data = upstream_response.json()
    except httpx.TimeoutException:
        return no_store({"error": "Upstream service timed out"}, 504)
    except (httpx.HTTPError, ValueError):
        app.logger.exception("Upstream request failed")
        return no_store({"error": "Upstream service unavailable"}, 502)

    if (
        not isinstance(upstream_data, dict)
        or upstream_data.get("status") != 200
        or not upstream_data.get("nickname")
    ):
        return no_store({
            "error": "Player not found",
            "upstream_response": upstream_data
        }, 404)

    return no_store({
        "status": "success",
        "message": "User information fetched successfully",
        "data": {
            "uid": uid,
            "nickname": upstream_data.get("nickname"),
            "game": upstream_data.get("game", game),
            "level": upstream_data.get("level"),
            "rank": upstream_data.get("rank"),
            "region": upstream_data.get("region", region),
            "status": "Active"
        }
    })


@app.errorhandler(404)
def not_found(_error):
    return no_store({
        "error": "Not found",
        "available_endpoints": [
            "/",
            "/api/health",
            "/api/player"
        ]
    }, 404)


@app.errorhandler(500)
def internal_error(_error):
    app.logger.exception("Unexpected server error")
    return no_store({"error": "Internal server error"}, 500)


# Vercel detects the Flask WSGI application named `app` in this root file.
# Do not add app.run() for Vercel deployment.
