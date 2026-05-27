#!/usr/bin/env python3
"""Send realistic fake room data to Firebase Realtime Database.

This script is useful when the Android app and Firebase database must be tested
before the physical Arduino nodes are ready.
"""

import argparse
import json
import random
import time
import urllib.error
import urllib.request


ROOMS = {
    "room1": "Aula 1",
    "room2": "Aula 2",
}


def build_payload(room_name):
    return {
        "name": room_name,
        "temperature": round(random.uniform(19.0, 27.0), 1),
        "humidity": round(random.uniform(35.0, 70.0), 0),
        "noise": round(random.uniform(20.0, 80.0), 0),
        "presence": random.choice([True, False]),
        "lastUpdate": int(time.time() * 1000),
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


def main():
    parser = argparse.ArgumentParser(description="Smart Study Rooms Firebase simulator")
    parser.add_argument(
        "--database-host",
        required=True,
        help="Firebase RTDB host without https://, for example project-default-rtdb.europe-west1.firebasedatabase.app",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Seconds between updates. Default: 5",
    )
    parser.add_argument(
        "--auth",
        default=None,
        help="Optional Firebase database secret or auth token for non-public rules.",
    )
    args = parser.parse_args()

    base_url = f"https://{args.database_host.rstrip('/')}/rooms"
    print("Smart Study Rooms simulator started")
    print(f"Database: {base_url}")
    print("Press CTRL+C to stop")

    while True:
        for room_id, room_name in ROOMS.items():
            payload = build_payload(room_name)
            url = f"{base_url}/{room_id}.json"
            if args.auth:
                url = f"{url}?auth={args.auth}"

            try:
                status, _ = put_json(url, payload)
                print(f"{room_id}: HTTP {status} -> {payload}")
            except urllib.error.URLError as exc:
                print(f"{room_id}: upload failed: {exc}")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
