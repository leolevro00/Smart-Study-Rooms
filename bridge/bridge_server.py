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
ROOM_NAMES = {
    "room1": "Aula 1",
    "room2": "Aula 2",
}
STUDY_PREFERENCES = {
    "balanced": {
        "label": "Bilanciata",
        "temperatureWeight": 35,
        "noiseWeight": 35,
        "humidityWeight": 20,
    },
    "comfort": {
        "label": "Priorita comfort",
        "temperatureWeight": 50,
        "noiseWeight": 25,
        "humidityWeight": 20,
    },
    "quiet": {
        "label": "Priorita silenzio",
        "temperatureWeight": 20,
        "noiseWeight": 55,
        "humidityWeight": 15,
    },
}


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


class BridgeState:
    def __init__(self, preference="balanced"):
        self.preference = preference
        self.rooms = {}
        self.scores = {}
        self.best_room_id = None
        self.actuators = {
            room_id: {"bestRoomLed": False}
            for room_id in ROOM_NAMES.keys()
        }

    def update_room(self, room_id, payload):
        self.rooms[room_id] = payload
        self.recalculate()

    def set_preference(self, preference):
        if preference not in STUDY_PREFERENCES or preference == self.preference:
            return False
        self.preference = preference
        self.recalculate()
        return True

    def recalculate(self):
        self.scores = {
            room_id: calculate_room_score(payload, self.preference)
            for room_id, payload in self.rooms.items()
        }
        if not self.scores:
            self.best_room_id = None
            self.actuators = {
                room_id: {"bestRoomLed": False}
                for room_id in ROOM_NAMES.keys()
            }
            return

        self.best_room_id = max(self.scores, key=self.scores.get)
        all_room_ids = set(ROOM_NAMES.keys()) | set(self.rooms.keys())
        self.actuators = {
            room_id: {"bestRoomLed": room_id == self.best_room_id}
            for room_id in all_room_ids
        }

    def actuator_state(self, room_id):
        return self.actuators.get(room_id, {"bestRoomLed": False})

    def recommendation_payload(self):
        if not self.best_room_id:
            return None
        payload = {
            "bestRoomId": self.best_room_id,
            "bestRoomName": ROOM_NAMES.get(self.best_room_id, self.best_room_id),
            "preference": self.preference,
            "preferenceLabel": STUDY_PREFERENCES[self.preference]["label"],
            "updatedAt": int(time.time() * 1000),
        }
        for room_id, score in self.scores.items():
            payload[f"{room_id}Score"] = score
        return payload


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

    clean_payload = {
        "name": name[:60],
        "temperature": required_number(payload, "temperature", -10, 50),
        "humidity": required_number(payload, "humidity", 0, 100),
        "noise": required_number(payload, "noise", 0, 100),
        "lastUpdate": timestamp,
        "source": "bridge",
    }
    if "presence" in payload:
        clean_payload["presence"] = required_bool(payload, "presence")
    return clean_payload


def calculate_room_score(room, preference="balanced"):
    # Mirrors Android RoomScoreCalculator weights for the selected preference.
    temperature_score = score_temperature(room.get("temperature"))
    noise_score = score_noise(room.get("noise"))
    humidity_score = score_humidity(room.get("humidity"))

    weights = STUDY_PREFERENCES[preference]
    score = (
        weighted_score(temperature_score, 35, weights["temperatureWeight"])
        + weighted_score(noise_score, 35, weights["noiseWeight"])
        + weighted_score(humidity_score, 20, weights["humidityWeight"])
    )
    return max(0, min(100, score))


def score_temperature(temperature):
    temperature = float(temperature)
    if 20 <= temperature <= 23:
        return 35
    if 18 <= temperature <= 25:
        return 25
    if 16 <= temperature <= 28:
        return 15
    return 5


def score_noise(noise):
    noise = float(noise)
    if noise <= 10:
        return 35
    if noise <= 20:
        return 22
    if noise <= 30:
        return 10
    return 3


def score_humidity(humidity):
    humidity = float(humidity)
    if 40 <= humidity <= 60:
        return 20
    if 30 <= humidity <= 70:
        return 12
    return 5


def weighted_score(component_score, component_max, weight):
    return int((component_score / component_max) * weight + 0.5)


def request_json(url, method="GET", payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url=url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        raw_body = response.read().decode("utf-8")
        return response.status, raw_body, json.loads(raw_body or "null")


def put_json(url, payload):
    status, raw_body, _ = request_json(url, method="PUT", payload=payload)
    return status, raw_body


def get_json(url):
    return request_json(url, method="GET")


class BridgeRequestHandler(BaseHTTPRequestHandler):
    config = None
    state = BridgeState()

    def do_GET(self):
        if self.path in ("/", "/health"):
            self.write_json(200, {"status": "ok", "service": "smart-study-rooms-bridge"})
            return
        actuator_room_id = self.extract_actuator_room_id()
        if actuator_room_id:
            self.refresh_preference_from_firebase()
            self.publish_recommendation_and_actuators()
            self.write_json(200, self.state.actuator_state(actuator_room_id))
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

            self.refresh_preference_from_firebase()
            self.state.update_room(room_id, clean_payload)
            recommendation_status = self.publish_recommendation_and_actuators()
            actuator_status = self.state.actuator_state(room_id)

            self.write_json(
                200,
                {
                    "status": "accepted",
                    "roomId": room_id,
                    "firebaseStatus": current_status,
                    "historyStatus": history_status,
                    "recommendationStatus": recommendation_status,
                    "score": self.state.scores.get(room_id),
                    "bestRoomId": self.state.best_room_id,
                    "actuator": actuator_status,
                    "payload": clean_payload,
                },
            )
        except ValidationError as exc:
            self.write_json(400, {"error": str(exc)})
        except urllib.error.URLError as exc:
            self.write_json(502, {"error": f"errore Firebase: {exc}"})
        except Exception as exc:
            self.write_json(500, {"error": f"errore bridge: {exc}"})

    def refresh_preference_from_firebase(self):
        try:
            _, _, preference = get_json(self.config.firebase_url("settings/studyPreference"))
        except urllib.error.URLError:
            return False
        if not isinstance(preference, str):
            return False
        return self.state.set_preference(preference)

    def publish_recommendation_and_actuators(self):
        recommendation = self.state.recommendation_payload()
        if not recommendation:
            return None
        recommendation_status, _ = put_json(
            self.config.firebase_url("recommendation"),
            recommendation,
        )
        for actuator_room_id, actuator_payload in self.state.actuators.items():
            put_json(
                self.config.firebase_url(f"actuators/{actuator_room_id}"),
                actuator_payload,
            )
        return recommendation_status

    def extract_room_id(self):
        path = urllib.parse.urlparse(self.path).path.strip("/")
        parts = path.split("/")
        if len(parts) != 2 or parts[0] != "rooms":
            raise ValidationError("usa POST /rooms/<room_id>")
        return validate_room_id(parts[1])

    def extract_actuator_room_id(self):
        path = urllib.parse.urlparse(self.path).path.strip("/")
        parts = path.split("/")
        if len(parts) == 2 and parts[0] == "actuators":
            return validate_room_id(parts[1])
        return None

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
    parser.add_argument(
        "--study-preference",
        choices=sorted(STUDY_PREFERENCES.keys()),
        default="balanced",
        help="Initial preference used before the app writes settings/studyPreference. Values: balanced, comfort or quiet. Default: balanced",
    )
    args = parser.parse_args()

    BridgeRequestHandler.config = BridgeConfig(
        database_host=args.database_host,
        auth_token=args.auth,
        save_history=not args.no_history,
    )
    BridgeRequestHandler.state = BridgeState(preference=args.study_preference)

    server = ThreadingHTTPServer((args.host, args.port), BridgeRequestHandler)
    print("Smart Study Rooms bridge started")
    print(f"Listening on http://{args.host}:{args.port}")
    print(f"Firebase: https://{args.database_host.rstrip('/')}")
    print(f"History enabled: {not args.no_history}")
    print(f"Initial study preference: {args.study_preference} ({STUDY_PREFERENCES[args.study_preference]['label']})")
    print("Firebase preference path: settings/studyPreference")
    print("Press CTRL+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBridge stopped")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

