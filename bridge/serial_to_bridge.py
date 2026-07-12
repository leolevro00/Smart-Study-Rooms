#!/usr/bin/env python3
"""Read an Arduino UNO serial JSON stream and forward it to the local bridge."""

import argparse
import json
import time
import urllib.error
import urllib.request

try:
    import serial
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: pyserial. Install it with: py -m pip install pyserial"
    ) from exc


REQUIRED_KEYS = {"name", "temperature", "humidity", "noise"}


def post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url=url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status, response.read().decode("utf-8")


def parse_serial_line(line):
    payload = json.loads(line)
    missing_keys = REQUIRED_KEYS - set(payload.keys())
    if missing_keys:
        raise ValueError(f"missing keys: {sorted(missing_keys)}")
    return payload


def main():
    parser = argparse.ArgumentParser(description="Arduino UNO serial to bridge forwarder")
    parser.add_argument("--port", required=True, help="Serial port, for example COM3 or /dev/ttyACM0")
    parser.add_argument("--room-id", default="room2", help="Room id used in the bridge URL. Default: room2")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate. Default: 115200")
    parser.add_argument("--bridge-url", default="http://localhost:3000", help="Bridge base URL. Default: http://localhost:3000")
    args = parser.parse_args()

    endpoint = f"{args.bridge_url.rstrip('/')}/rooms/{args.room_id}"
    print("Arduino serial forwarder started")
    print(f"Serial: {args.port} at {args.baud} baud")
    print(f"Bridge endpoint: {endpoint}")
    print("Press CTRL+C to stop")

    with serial.Serial(args.port, args.baud, timeout=2) as serial_port:
        time.sleep(2)
        while True:
            raw_line = serial_port.readline().decode("utf-8", errors="replace").strip()
            if not raw_line:
                continue

            print(f"Serial <- {raw_line}")
            try:
                payload = parse_serial_line(raw_line)
                status, response = post_json(endpoint, payload)
                print(f"Bridge -> HTTP {status}: {response}")
            except json.JSONDecodeError as exc:
                print(f"Invalid JSON from Arduino: {exc}")
            except ValueError as exc:
                print(f"Invalid payload from Arduino: {exc}")
            except urllib.error.URLError as exc:
                print(f"Bridge upload failed: {exc}")


if __name__ == "__main__":
    main()
