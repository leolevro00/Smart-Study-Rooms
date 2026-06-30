#!/usr/bin/env python3
"""Smart Study Rooms local bridge.

The bridge receives room readings from Arduino nodes over the local network,
validates them, adds a trusted timestamp, and forwards clean data to Firebase.
It can also store a time-series copy under history/<room_id>/<timestamp>.
"""

import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


ROOM_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,40}$")


class ValidationError(Exception):
    pass


class BridgeConfig:
    def __init__(self, database_host, auth_token=None, save_history=True):
        self.database_host = database_host.rstrip("/")
        self.auth_token = auth_token
        self.save_history = save_history

    def firebase_url(self, path):
        url = f"https://{self.database_host}/{path.lstrip('/')}.json"
        if self.auth_token:
            url += "?auth=" + urllib.parse.quote(self.auth_token)
        return url


def validate_room_id(room_id):
    if not ROOM_ID_PATTERN.match(room_id):
        raise ValidationError("room id non valido")
    return room_id


def required_number(payload, key, minimum, maximum):
    value = payload.get(key)
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{key} deve essere numerico")
    if value < minimum or value > maximum:
        raise ValidationError(f"{key} fuori range: {value}")
    return round(float(value), 1)


def required_bool(payload, key):
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ValidationError(f"{key} deve essere true/false")
    return value


def validate_payload(room_id, payload):
    if not isinstance(payload, dict):
        raise ValidationError("payload JSON non valido")

    timestamp = int(time.time() * 1000)
    name = payload.get("name") or room_id
    if not isinstance(name, str):
        raise ValidationError("name deve essere una stringa")

    return {
        "name": name[:60],
        "temperature": required_number(payload, "temperature", -10, 50),
        "humidity": required_number(payload, "humidity", 0, 100),
        "noise": required_number(payload, "noise", 0, 100),
        "presence": required_bool(payload, "presence"),
        "lastUpdate": timestamp,
        "source": "bridge",
    }


def put_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url=url,
        data=data,
        method="PUT",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status, response.read().decode("utf-8")


class BridgeRequestHandler(BaseHTTPRequestHandler):
    config = None

    def do_GET(self):
        if self.path in ("/", "/health"):
            self.write_json(200, {"status": "ok", "service": "smart-study-rooms-bridge"})
            return
        self.write_json(404, {"error": "endpoint non trovato"})

    def do_POST(self):
        try:
            room_id = self.extract_room_id()
            payload = self.read_json_body()
            clean_payload = validate_payload(room_id, payload)

            current_url = self.config.firebase_url(f"rooms/{room_id}")
            current_status, _ = put_json(current_url, clean_payload)

            history_status = None
            if self.config.save_history:
                timestamp = clean_payload["lastUpdate"]
                history_url = self.config.firebase_url(f"history/{room_id}/{timestamp}")
                history_status, _ = put_json(history_url, clean_payload)

            self.write_json(
                200,
                {
                    "status": "accepted",
                    "roomId": room_id,
                    "firebaseStatus": current_status,
                    "historyStatus": history_status,
                    "payload": clean_payload,
                },
            )
        except ValidationError as exc:
            self.write_json(400, {"error": str(exc)})
        except urllib.error.URLError as exc:
            self.write_json(502, {"error": f"errore Firebase: {exc}"})
        except Exception as exc:
            self.write_json(500, {"error": f"errore bridge: {exc}"})

    def extract_room_id(self):
        path = urllib.parse.urlparse(self.path).path.strip("/")
        parts = path.split("/")
        if len(parts) != 2 or parts[0] != "rooms":
            raise ValidationError("usa POST /rooms/<room_id>")
        return validate_room_id(parts[1])

    def read_json_body(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise ValidationError("body JSON mancante")

        raw_body = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"JSON non valido: {exc}") from exc

    def write_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string, *args):
        print(f"{self.address_string()} - {format_string % args}")


def main():
    parser = argparse.ArgumentParser(description="Smart Study Rooms local bridge")
    parser.add_argument(
        "--database-host",
        required=True,
        help="Firebase RTDB host without https://, for example project-default-rtdb.europe-west1.firebasedatabase.app",
    )
    parser.add_argument("--auth", default=None, help="Optional Firebase database secret or auth token")
    parser.add_argument("--host", default="0.0.0.0", help="Bridge bind address. Default: 0.0.0.0")
    parser.add_argument("--port", type=int, default=3000, help="Bridge port. Default: 3000")
    parser.add_argument("--no-history", action="store_true", help="Disable writes under history/")
    args = parser.parse_args()

    BridgeRequestHandler.config = BridgeConfig(
        database_host=args.database_host,
        auth_token=args.auth,
        save_history=not args.no_history,
    )

    server = ThreadingHTTPServer((args.host, args.port), BridgeRequestHandler)
    print("Smart Study Rooms bridge started")
    print(f"Listening on http://{args.host}:{args.port}")
    print(f"Firebase: https://{args.database_host.rstrip('/')}")
    print(f"History enabled: {not args.no_history}")
    print("Press CTRL+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBridge stopped")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
