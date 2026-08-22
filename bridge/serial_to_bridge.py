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
        return response.status, raw_body, json.loads(raw_body or "{}")


def post_json(url, payload):
    return request_json(url, method="POST", payload=payload)


def get_json(url):
    return request_json(url, method="GET")


def apply_actuator_state(serial_port, state, last_state, force=False):
    best_room_led = bool(state.get("bestRoomLed", False))
    if best_room_led == last_state and not force:
        return last_state

    command = "BEST_LED_ON" if best_room_led else "BEST_LED_OFF"
    serial_port.write((command + "\n").encode("utf-8"))
    serial_port.flush()
    print(f"Serial -> {command}")
    return best_room_led


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
    parser.add_argument(
        "--actuator-poll-interval",
        type=float,
        default=2.0,
        help="Seconds between actuator state checks. Default: 2.0",
    )
    args = parser.parse_args()

    bridge_base_url = args.bridge_url.rstrip("/")
    endpoint = f"{bridge_base_url}/rooms/{args.room_id}"
    actuator_endpoint = f"{bridge_base_url}/actuators/{args.room_id}"
    print("Arduino serial forwarder started")
    print(f"Serial: {args.port} at {args.baud} baud")
    print(f"Bridge endpoint: {endpoint}")
    print(f"Actuator endpoint: {actuator_endpoint}")
    print("Press CTRL+C to stop")

    with serial.Serial(args.port, args.baud, timeout=2) as serial_port:
        time.sleep(2)
        last_best_led_state = None
        last_actuator_poll = 0

        while True:
            now = time.monotonic()
            raw_line = serial_port.readline().decode("utf-8", errors="replace").strip()

            if raw_line:
                print(f"Serial <- {raw_line}")
                try:
                    payload = parse_serial_line(raw_line)
                    status, response, response_json = post_json(endpoint, payload)
                    print(f"Bridge -> HTTP {status}: {response}")
                    if "actuator" in response_json:
                        last_best_led_state = apply_actuator_state(
                            serial_port,
                            response_json["actuator"],
                            last_best_led_state,
                        )
                except json.JSONDecodeError as exc:
                    print(f"Invalid JSON from Arduino: {exc}")
                except ValueError as exc:
                    print(f"Invalid payload from Arduino: {exc}")
                except urllib.error.URLError as exc:
                    print(f"Bridge upload failed: {exc}")

            if now - last_actuator_poll >= args.actuator_poll_interval:
                last_actuator_poll = now
                try:
                    _, _, actuator_state = get_json(actuator_endpoint)
                    last_best_led_state = apply_actuator_state(
                        serial_port,
                        actuator_state,
                        last_best_led_state,
                        force=True,
                    )
                except urllib.error.URLError as exc:
                    print(f"Actuator poll failed: {exc}")
                except json.JSONDecodeError as exc:
                    print(f"Invalid actuator response from bridge: {exc}")


if __name__ == "__main__":
    main()

